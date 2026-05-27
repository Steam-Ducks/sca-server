import re
import glob


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    content = re.sub(
        r"APIClient\(\)\.(get|post|put|delete|patch)\(", r"api_client.\1(", content
    )

    def add_param(m):
        sig = m.group(0)
        if "api_client" in sig:
            return sig
        sig = re.sub(r"def (test_\w+)\(self\):", r"def \1(self, api_client):", sig)
        sig = re.sub(
            r"def (test_\w+)\(self, (?!api_client)", r"def \1(self, api_client, ", sig
        )
        return sig

    content = re.sub(r"    def test_\w+\(self[^)]*\):", add_param, content)

    def fix_no_auth(m):
        block = m.group(0)
        block = re.sub(r"\(self, api_client(?:, )?\)", "(self):", block, count=1)
        block = re.sub(r"\(self, api_client, ", "(self, ", block, count=1)
        block = block.replace("api_client.get(", "APIClient().get(")
        block = block.replace("api_client.post(", "APIClient().post(")
        block = block.replace("== 403", "== 401")
        return block

    content = re.sub(
        r"    def test_\w*(?:sem_autenticacao|retorna_403|without_auth|unauthenticated)\w*\([^)]*\):.*?(?=\n    def |\nclass |\Z)",
        fix_no_auth,
        content,
        flags=re.DOTALL,
    )

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Fixed: {path}")
    else:
        print(f"—  No changes: {path}")


for path in glob.glob("**/tests/integration/test_*.py", recursive=True):
    fix_file(path)

print("\nDone.")
