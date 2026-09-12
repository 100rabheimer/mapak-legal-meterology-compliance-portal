import os
import zipfile

def create_zip(source_dir, output_zip):
    # Directories and files to exclude
    EXCLUDE_DIRS = {
        'node_modules',
        '.git',
        '__pycache__',
        '.venv',
        'venv',
        'dist',
        '.vscode',
        '.idea'
    }
    EXCLUDE_EXTS = {'.pyc', '.pyo', '.log'}
    EXCLUDE_FILES = {os.path.basename(output_zip)}

    print(f"Creating zip file at: {output_zip}")
    file_count = 0

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            
            for file in files:
                if file in EXCLUDE_FILES or file.startswith('.'):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue
                
                full_path = os.path.join(root, file)
                # Compute relative path inside the zip
                rel_path = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, arcname=os.path.join("Mapak", rel_path))
                file_count += 1
                if file_count % 100 == 0:
                    print(f"Archived {file_count} files...")

    zip_size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"\nDone! Successfully archived {file_count} files into '{output_zip}' ({zip_size_mb:.2f} MB).")

if __name__ == '__main__':
    project_dir = os.path.dirname(os.path.abspath(__file__))
    # Output to project root
    workspace_zip = os.path.join(project_dir, "Mapak_Project.zip")
    create_zip(project_dir, workspace_zip)
    
    # Also copy/ensure it exists on Desktop
    try:
        desktop_dir = os.path.abspath(os.path.join(project_dir, ".."))
        desktop_zip = os.path.join(desktop_dir, "Mapak_Project.zip")
        if desktop_zip != workspace_zip:
            import shutil
            shutil.copy2(workspace_zip, desktop_zip)
            print(f"Also copied to Desktop: {desktop_zip}")
    except Exception as e:
        print(f"Could not copy to Desktop: {e}")
