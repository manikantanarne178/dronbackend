from app.utils import UploadFile, save_upload


def test_utils_exports_are_available():
    assert UploadFile is not None
    assert callable(save_upload)
