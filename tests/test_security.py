"""
AL 自学系统 —— 核心安全与工具函数单元测试

运行：python -m unittest discover tests   （在 AL-Learning-System 目录下）
或：  python tests/test_security.py
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_HERE)
sys.path.insert(0, _APP_DIR)

os.environ["APP_SECRET_KEY"] = "test-secret-key-for-unit-test-ONLY"

import server as S


class TestPasswordHash(unittest.TestCase):
    def test_new_hash_format(self):
        h = S.hash_password_new("mypassword")
        self.assertTrue(h.startswith("pbkdf2$"))
        parts = h.split("$")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2")
        self.assertEqual(int(parts[1]), S._PBKDF2_ITER)

    def test_verify_correct_password(self):
        h = S.hash_password_new("correct123")
        self.assertTrue(S.verify_password("correct123", h))

    def test_verify_wrong_password(self):
        h = S.hash_password_new("correct123")
        self.assertFalse(S.verify_password("wrong", h))

    def test_verify_empty_stored(self):
        self.assertFalse(S.verify_password("x", ""))
        self.assertFalse(S.verify_password("x", None))

    def test_verify_malformed_pbkdf2(self):
        self.assertFalse(S.verify_password("x", "pbkdf2$abc"))
        self.assertFalse(S.verify_password("x", "pbkdf2$100$nothex$nothex"))

    def test_different_salts(self):
        h1 = S.hash_password_new("same")
        h2 = S.hash_password_new("same")
        self.assertNotEqual(h1, h2, "相同密码应产生不同哈希（随机盐）")

    def test_legacy_detection(self):
        legacy = S.hash_password("alice", "pass")
        self.assertTrue(S.is_legacy_hash(legacy))
        new = S.hash_password_new("pass")
        self.assertFalse(S.is_legacy_hash(new))
        self.assertFalse(S.is_legacy_hash(""))


class TestSecretCodec(unittest.TestCase):
    def test_roundtrip(self):
        for plain in ("", "sk-abc123", "deepseek-key-xyz", "中文密钥测试"):
            stored = S.enc_secret(plain)
            self.assertEqual(S.dec_secret(stored), plain)

    def test_enc_prefix(self):
        stored = S.enc_secret("sk-test")
        self.assertTrue(stored.startswith("enc$"))

    def test_dec_plain_passthrough(self):
        self.assertEqual(S.dec_secret("sk-plain"), "sk-plain")
        self.assertEqual(S.dec_secret(""), "")

    def test_dec_malformed(self):
        self.assertEqual(S.dec_secret("enc$!!!notbase64!!!"), "")


class TestCorsConfig(unittest.TestCase):
    def test_default_allows_all(self):
        os.environ.pop("ALLOWED_ORIGINS", None)
        import importlib
        importlib.reload(S)
        self.assertIn("*", S.ALLOWED_ORIGINS)

    def test_explicit_origins(self):
        os.environ["ALLOWED_ORIGINS"] = "https://a.com,https://b.com"
        import importlib
        importlib.reload(S)
        self.assertEqual(S.ALLOWED_ORIGINS, ["https://a.com", "https://b.com"])
        self.assertNotIn("*", S.ALLOWED_ORIGINS)
        os.environ.pop("ALLOWED_ORIGINS", None)


class TestMasteryLabels(unittest.TestCase):
    def test_labels_complete(self):
        for lv in (0, 1, 2, 3, 4):
            self.assertIn(lv, S.MASTERY_LABEL)

    def test_verdict_mapping(self):
        self.assertEqual(S.VERDICT_LEVEL["掌握"], 4)
        self.assertEqual(S.VERDICT_LEVEL["未掌握"], 1)


if __name__ == "__main__":
    unittest.main()