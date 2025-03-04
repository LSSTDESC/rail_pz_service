import os
import subprocess
from urllib.request import urlretrieve


def setup_test_area() -> int:
    """Download test files to setup a project testsing area

    Returns
    -------
    int
       0 for success, error code otherwise

    Notes
    -----
    This will download files into 'tests/temp_data', and could take a few
    minutes.

    This will not download the files if they are already present
    """

    if not os.path.exists("tests/pz_rail_server.tgz"):
        urlretrieve(
            "http://s3df.slac.stanford.edu/people/echarles/xfer/pz_rail_server.tgz",
            "tests/pz_rail_server.tgz",
        )
        if not os.path.exists("tests/pz_rail_server.tgz"):
            return 1

    if not os.path.exists("test/temp_data/inputs"):
        status = subprocess.run(["tar", "zxvf", "tests/pz_rail_server.tgz", "-C", "tests"], check=False)
        if status.returncode != 0:
            return status.returncode

    if not os.path.exists("tests/temp_data/inputs/minimal_gold_test.hdf5"):
        return 2

    return 0


def teardown_test_area() -> None:
    if not os.environ.get("NO_TEARDOWN"):
        os.system("\\rm -rf tests/temp_data")
        try:
            os.unlink("tests/pz_rail_server.tgz")
        except FileNotFoundError:
            pass
