from pathlib import Path

# Project root (run this script from the project root)
ROOT = Path.cwd()

folders = [
    ROOT / "modules" / "master_data",
    ROOT / "modules" / "master_data" / "clients",
    ROOT / "modules" / "master_data" / "projects",
    ROOT / "modules" / "master_data" / "sites",
]

files = [
    ROOT / "modules" / "master_data" / "__init__.py",

    ROOT / "modules" / "master_data" / "clients" / "__init__.py",
    ROOT / "modules" / "master_data" / "clients" / "client_repository.py",
    ROOT / "modules" / "master_data" / "clients" / "client_service.py",
    ROOT / "modules" / "master_data" / "clients" / "client_view.py",

    ROOT / "modules" / "master_data" / "projects" / "__init__.py",
    ROOT / "modules" / "master_data" / "projects" / "project_repository.py",
    ROOT / "modules" / "master_data" / "projects" / "project_service.py",
    ROOT / "modules" / "master_data" / "projects" / "project_view.py",

    ROOT / "modules" / "master_data" / "sites" / "__init__.py",
    ROOT / "modules" / "master_data" / "sites" / "site_repository.py",
    ROOT / "modules" / "master_data" / "sites" / "site_service.py",
    ROOT / "modules" / "master_data" / "sites" / "site_view.py",
]

# Create folders
for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)

# Create files
for file in files:
    if not file.exists():
        file.write_text(
            f'"""\n{file.stem}\nJCAP Construction Suite\n"""\n',
            encoding="utf-8"
        )

print("=" * 60)
print("Master Data module created successfully.")
print("=" * 60)
print()

for folder in folders:
    print(f"[DIR ] {folder.relative_to(ROOT)}")

for file in files:
    print(f"[FILE] {file.relative_to(ROOT)}")

print()
print("Done.")