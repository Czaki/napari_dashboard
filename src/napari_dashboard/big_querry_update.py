import os.path
from dataclasses import dataclass
from importlib.metadata import distribution
from tqdm import tqdm

import pandas as pd
from packaging import version

from napari_dashboard.db_schema.pypi import PyPi

QUERRY = """
SELECT
  timestamp,
  country_code,
  file.filename AS project,
  details.python AS python,
  details.system.name AS system,
  details.system.release AS system_release,
  details.distro.name AS distro_name,
  details.distro.version AS distro_version,
FROM
  `bigquery-public-data.pypi.file_downloads`
WHERE
  file.project = 'napari'
  AND details.installer. name = 'pip'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY
  timestamp;
"""


@dataclass
class ProjectInfo:
    name: str
    version: version.Version
    wheel: bool


def parse_file_name(file_name: str) -> ProjectInfo:
    """
    Parse the file name to get the project name, version and if it is a wheel file

    Parameters
    ----------
    file_name: str
        The name of the file to parse. The file need to be valid entry from
        the PyPi database. For example:
        napari-0.5.4.tar.gz
        napari-0.5.4-py3-none-any.whl

    Returns
    -------
    ProjectInfo
        The parsed information
    """
    name, ext = os.path.splitext(file_name)
    wheel = ext == ".whl"

    name, version_, _ = file_name.split("-", 2)
    return ProjectInfo(name, version.parse(version_), wheel)


def is_ci_install(system_release: str) -> bool:
    if "azure" in system_release:
        return True
    if "amzn" in system_release:
        return True
    if "aws" in system_release:
        return True
    if "gcp" in system_release:
        return True
    if "cloud-amd64" in system_release:
        return True
    return False


def load_from_query_file(querry_file: str):
    df = pd.read_csv(querry_file)
    for row in df.iterrows():
        project_info = parse_file_name(row[1].project)
        is_ci = is_ci_install(row[1].system_release)
        # print(row)
        obj = PyPi(
            timestamp=row[1].timestamp,
            country_code=row[1].country_code,
            project=project_info.name,
            version=str(project_info.version),
            python_version=row[1].python,
            system_name=row[1].system,
            system_release=row[1].system_release,
            distro_name=row[1].distro_name,
            distro_version=row[1].distro_version,
            wheel=project_info.wheel,
            ci_install=is_ci,
        )
        print(obj)
        if row[0] > 100:
            break


def get_version_from_beginning(details: str, with_pre=True) -> tuple[str, str]:
    """
    Get the version from the beginning of the string.

    Parameters
    ----------
    details: str
        The string to parse

    Returns
    -------
    Tuple[str, str]
        The version and the rest of the string

    """
    if with_pre:
        suffix_li = ["rc", "a", "b", "dev", "post"]
    else:
        suffix_li = []
    i = 0
    while i < len(details):
        if details[i].isalpha():
            for suffix in suffix_li:
                if details[i:].startswith(suffix):
                    i+=len(suffix)
                    break
            else:
                return details[:i], details[i:]
        else:
            i += 1
    return details, ""


def get_name_from_begin(details: str) -> tuple[str, str]:
    """
    Get the name from the beginning of the string.

    Parameters
    ----------
    details: str
        The string to parse

    Returns
    -------
    Tuple[str, str]
        The name and the rest of the string

    """
    for i in range(len(details)):
        if details[i].isdigit():
            return details[:i], details[i:]
    return details, ""


def parse_distro(distro: str):
    """
    Parse the distro string to get the name and version

    Parameters
    ----------
    distro: str
        The distro string to parse. For example:
        Ubuntu22.04jammy

    Returns
    -------
    Tuple[str, str]
        The distro name and version
    """
    for i in range(len(distro)):
        if distro[i].isdigit():
            distro_name = distro[:i]
            for j in range(i, len(distro)):
                if distro[j].isalpha():
                    distro_version = distro[i:j]
                    return distro_name, distro_version
    else:
        raise ValueError("No version found in distro string")


def parse_system_from_string(details: str) -> tuple[str, str, str, str]:
    """
    Parse the system string to get the name and version

    Parameters
    ----------
    details: str
        The system string to parse. For example:
        Linux5.10.16.3-microsoft-standard-WSL2x86_64

    Returns
    -------
    """
    for el in ("x86_64", "arm64", "AMD64", "i386", "OpenSSL", "iPad"):
        if el in details:
            details = details[: details.rfind(el)]
            break
    distribution_name, details = get_name_from_begin(details)
    if distribution_name.startswith("WindowsVista"):
        return "Windows", "Vista", "", ""
    if distribution_name.startswith("WindowsME"):
        return "Windows", "Me", "", ""
    if distribution_name.startswith("CYGWIN"):
        return "Cygwin", "", "", ""
    if distribution_name.startswith("MSYS"):
        return "MSYS", "", "", ""
    if distribution_name == "Windows":
        return distribution_name, details, "", ""

    distribution_version, details = get_version_from_beginning(details, with_pre=False)

    if distribution_name.startswith("Darwin"):
        return "", "", "Darwin", distribution_version

    if distribution_name == "iOS":
        name, version = get_name_from_begin(details)
        return distribution_name, distribution_version, name, version

    if distribution_name in ("macOS", "OS X"):
        system_name, details = get_name_from_begin(details)
        assert system_name == "Darwin"
        system_version, details = get_version_from_beginning(details, with_pre=False)
        return distribution_name, distribution_version, system_name, system_version

    if distribution_name == "Linux":
        return distribution_name, distribution_version, "", ""

    if "BSD" in distribution_name:
        return distribution_name, distribution_version, "", ""

    if "Linux" not in details:
        raise ValueError("System name not found")


    # we are in linux case
    linux_pos = details.find("Linux")
    linux_end = linux_pos + len("Linux")
    return distribution_name, distribution_version, "Linux", details[linux_end:]


def parse_python_from_string(details: str) -> tuple[str, str, str, str]:
    """
    Split string like this:

    pip23.0.13.10.6CPython3.10.6Ubuntu22.04jammyglibc2.35Linux5.10.16.3-microsoft-standard-WSL2x86_64OpenSSL 3.0.2 15 Mar 202267.4.01.67.1
    """
    python_str_li = ["CPython", "PyPy", "GraalVM"]

    for python_str in python_str_li:
        python_pos = details.find(python_str)
        if python_pos != -1:
            python_version = details[:python_pos]
            python_implementation = python_str
            python_implementation_version, details = (
                get_version_from_beginning(
                    details[python_pos + len(python_str) :]
                )
            )
            break
    else:
        raise ValueError("Python version not found")

    return (
        python_version,
        python_implementation,
        python_implementation_version,
        details,
    )


def parse_details(row):
    # Parse strings like
    # pip21.33.8.3CPython3.8.3Windows7OpenSSL 1.1.1f  31 Mar 202062.1.0
    # pip23.0.13.10.6CPython3.10.6Ubuntu22.04jammyglibc2.35Linux5.10.16.3-microsoft-standard-WSL2x86_64OpenSSL 3.0.2 15 Mar 202267.4.01.67.1
    # pip20.3.13.7.4CPython3.7.4macOS10.12.6Darwin16.7.0x86_64OpenSSL 1.1.1d  10 Sep 201951.0.0

    details_str = row.DETAILS_ALL
    details_str = details_str[
        len(row.DETAILS_INSTALLER_NAME) + len(row.DETAILS_INSTALLER_VERSION) :
    ]

    (
        python_version,
        python_implementation,
        python_implementation_version,
        details_str,
    ) = parse_python_from_string(details_str)
    distro_name, distro_version, system_name, system_version = (
        parse_system_from_string(details_str)
    )
    return (
        python_version,
        python_implementation,
        python_implementation_version,
        system_name,
        system_version,
        distro_name,
        distro_version,
    )


def load_from_czi_file(czi_file: str) -> pd.DataFrame:
    dkt = {"Darwin": False, "Linux": False, "Windows": False}
    df = pd.read_csv(czi_file)
    for row in tqdm(df.iterrows(), total=len(df)):
        (
            python_version,
            python_implementation,
            python_implementation_version,
            system_name,
            system_version,
            distro_name,
            distro_version,
        ) = parse_details(row[1])

        # print(row[1])
        # print(row[1].DETAILS_ALL)
        is_ci = is_ci_install(row[1].DETAILS_ALL)
        parse_python_from_string(row[1].DETAILS_ALL)
        obj = PyPi(
            timestamp=row[1].TIMESTAMP,
            country_code=row[1].COUNTRY_CODE,
            project=row[1].PROJECT,
            version=row[1].FILE_VERSION,
            python_version=python_version,
            system_name=system_name,
            system_release=system_version,
            distro_name=distro_name,
            distro_version=distro_version,
            wheel=row[1].FILE_TYPE == "bdist_wheel",
            ci_install=is_ci,
        )


def main():
    # load_from_query_file("data/bquxjob_510c5b0e_193014da029.csv")
    load_from_czi_file("data/bigquery_installs_2024-10-01.csv")


if __name__ == "__main__":
    main()
