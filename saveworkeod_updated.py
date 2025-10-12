import os
import subprocess
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'git_save.log'))  # Output to file
    ]
)
logger = logging.getLogger("SaveWorkEOD")

# Patterns for sensitive information
SENSITIVE_PATTERNS = [
    (r'password\s*=\s*[\'\"][^\'\"\s]+[\'\"]', 'potential password'),
    (r'api[_-]?key\s*=\s*[\'\"][^\'\"\s]+[\'\"]', 'API key'),
    (r'secret\s*=\s*[\'\"][^\'\"\s]+[\'\"]', 'secret key'),
    (r'access[_-]?token\s*=\s*[\'\"][^\'\"\s]+[\'\"]', 'access token'),
    (r'auth[_-]?token\s*=\s*[\'\"][^\'\"\s]+[\'\"]', 'auth token'),
    (r'bearer\s*[\'\"][^\'\"\s]+[\'\"]', 'bearer token'),
    (r'BEGIN\s+PRIVATE\s+KEY', 'private key'),
    (r'BEGIN\s+RSA\s+PRIVATE\s+KEY', 'RSA private key'),
]

# File size threshold (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def run_command(command):
    """Runs a shell command and returns the output."""
    logger.info(f"Executing command: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        logger.info(f"Command successful: {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error details: {e.stderr}")
        print(f"❌ Error running command: {command}\n{e.stderr}")
        return None

def get_current_branch():
    """Fetches the current Git branch dynamically."""
    logger.info("Getting current branch...")
    branch = run_command("git rev-parse --abbrev-ref HEAD")
    if branch:
        logger.info(f"Current branch: {branch}")
        return branch
    else:
        logger.warning("Failed to get current branch, defaulting to 'main'")
        return "main"

def check_git_status():
    """Checks the Git status to see if there are changes."""
    logger.info("Checking Git status for changes...")
    print("🔍 Checking for changes...")
    status = run_command("git status --porcelain")
    
    if status:
        file_count = len(status.splitlines())
        logger.info(f"Found {file_count} changed file(s)")
        return status
    else:
        logger.info("No changes found in working directory")
        return None

def quick_branch_choice():
    """Simple choice between main branch or new branch."""
    current_branch = get_current_branch()
    logger.info(f"Presenting branch options (current: {current_branch})")
    
    print(f"\n🔀 Current branch: {current_branch}")
    print("\n📋 COMMIT OPTIONS:")
    print("  1️⃣  Commit to main branch")
    print("  2️⃣  Commit to new branch")
    
    choice = input("\n👉 Your choice (1 or 2): ").strip()
    logger.info(f"User selected option: {choice}")
    
    if choice == "1":
        # Handle main branch
        if current_branch != "main":
            logger.info("Switching from current branch to main branch")
            print("🔄 Switching to main branch...")
            if not run_command("git checkout main"):
                logger.error("Failed to switch to main branch")
                print("❌ Failed to switch to main branch")
                return None
        logger.info("Using main branch for commit")
        print("✅ Using main branch")
        return "main"
    
    elif choice == "2":
        # Handle new branch
        suggested_name = f"update-{datetime.now().strftime('%Y%m%d')}"
        logger.info(f"Suggesting branch name: {suggested_name}")
        
        new_branch = input(f"👉 Enter new branch name (or press Enter for '{suggested_name}'): ")
        
        if not new_branch.strip():
            logger.info(f"No name provided, using suggested name: {suggested_name}")
            new_branch = suggested_name
            
        logger.info(f"Creating new branch: {new_branch}")
        print(f"🔄 Creating and switching to branch: {new_branch}")
        
        # Modified condition: check if command didn't fail (result is not None)
        result = run_command(f"git checkout -b {new_branch}")
        if result is not None:  # Changed from 'if result:'
            logger.info(f"Successfully created and switched to branch: {new_branch}")
            return new_branch
        
        logger.error(f"Failed to create/switch to branch: {new_branch}")
        return None
    
    else:
        logger.warning(f"Invalid choice entered: {choice}")
        print("❌ Invalid choice. Please enter 1 or 2.")
        return None

def ensure_all_changes_staged():
    """Make sure there are no unstaged changes remaining."""
    unstaged = run_command("git diff --name-only")
    if unstaged:
        logger.warning(f"Found unstaged changes after git add, attempting to stage them")
        return run_command("git add .")
    return True

def check_for_sensitive_info():
    """Checks staged changes for sensitive information and large files."""
    logger.info("Checking for sensitive information in staged changes...")
    print("🔍 Checking for sensitive information...")
    
    # Get list of staged files
    staged_files = run_command("git diff --cached --name-only")
    if not staged_files:
        return True
    
    staged_files_list = staged_files.splitlines()
    warnings = []
    
    # Check each staged file
    for file_path in staged_files_list:
        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            continue
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                warnings.append(f"⚠️  Large file detected: {file_path} ({file_size // 1024 // 1024}MB)")
        except OSError:
            logger.warning(f"Could not check size of {file_path}")
        
        # Check for binary files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    content = f.read()
                    
                    # Check for sensitive patterns
                    for pattern, description in SENSITIVE_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            warnings.append(f"⚠️  Possible {description} found in {file_path}")
                            break
                except UnicodeDecodeError:
                    # Binary file, skip content check
                    pass
        except OSError:
            logger.warning(f"Could not read {file_path}")
    
    # If warnings found, ask user what to do
    if warnings:
        print("\n⚠️  POTENTIAL SENSITIVE INFORMATION DETECTED:")
        for warning in warnings:
            print(warning)
        
        choice = input("\n⚠️  Do you want to proceed with the commit? (y/n): ").strip().lower()
        if choice != 'y':
            logger.info("User aborted commit due to sensitive information warnings")
            print("🛑 Commit aborted. Please review the files and try again.")
            return False
        
        logger.info("User chose to proceed despite sensitive information warnings")
        print("⚠️  Proceeding with commit despite warnings...")
    
    return True

def stage_changes():
    """Stages all changes."""
    logger.info("Staging changes...")
    print("📂 Staging all changes...")
    result = run_command("git add .")
    
    if result is not None:
        logger.info("Successfully ran git add command")
        # Verify staging worked by checking git status
        staged = run_command("git status -s")
        if staged:
            logger.info(f"Staged files: \n{staged}")
            
        # Double-check for any remaining unstaged changes
        ensure_all_changes_staged()
        return True
    else:
        logger.error("Failed to stage changes")
        return False

def commit_changes():
    """Commits changes with a user-provided or default message."""
    # Check for sensitive information before committing
    if not check_for_sensitive_info():
        return False
        
    default_msg = f"Update {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    logger.info(f"Preparing to commit with default message: {default_msg}")
    
    commit_message = input(f"📝 Enter commit message (or press Enter for '{default_msg}'): ") or default_msg
    logger.info(f"Using commit message: {commit_message}")
    
    print(f"💾 Committing changes: \"{commit_message}\"")
    result = run_command(f'git commit -m "{commit_message}"')
    
    if result:
        logger.info("Commit successful")
        logger.info(f"Commit details: {result}")
        return True
    else:
        logger.error("Commit failed")
        return False

def pull_latest_changes(branch):
    """Pulls latest changes before pushing to avoid conflicts."""
    logger.info(f"Pulling latest changes from {branch}...")
    print(f"🔄 Pulling latest changes from {branch}...")
    
    # First check if we have unstaged changes
    unstaged = run_command("git diff --name-only")
    if unstaged:
        logger.warning("Cannot pull: unstaged changes detected")
        print("⚠️ Cannot pull: You have unstaged changes")
        
        # Try to stage these changes
        if run_command("git add ."):
            logger.info("Successfully staged remaining changes")
            
            # Try to commit these changes
            temp_result = run_command('git commit -m "Auto-commit unstaged changes"')
            if temp_result:
                logger.info("Auto-committed unstaged changes")
            else:
                logger.error("Failed to auto-commit unstaged changes")
                return False
        else:
            logger.error("Failed to stage unstaged changes")
            return False
    
    # Now try to pull
    result = run_command(f"git pull origin {branch}")
    
    if result:
        logger.info("Successfully pulled latest changes")
        logger.info(f"Pull details: {result}")
        return True
    else:
        logger.warning(f"Failed to pull latest changes from {branch}")
        return False

def push_changes(branch):
    """Pushes changes to GitHub."""
    logger.info(f"Pushing changes to branch: {branch}")
    print(f"🚀 Pushing to GitHub ({branch})...")
    result = run_command(f"git push origin {branch}")
    
    # Check for "up-to-date" message in stderr when command fails
    if result is None:
        # Re-run without check=True to capture output even when git reports up-to-date
        process = subprocess.run(f"git push origin {branch}", shell=True, text=True, capture_output=True)
        if "Everything up-to-date" in process.stderr or "Everything up-to-date" in process.stdout:
            logger.info(f"Branch {branch} is already up to date with remote")
            print(f"✅ Branch '{branch}' is already up to date with remote")
            return True
        else:
            logger.error(f"Failed to push changes to {branch}")
            return False
    
    logger.info(f"Successfully pushed changes to {branch}")
    if result:
        logger.info(f"Push details: {result}")
    return True

def main():
    """Runs the full Git automation process."""
    logger.info("=== SAVE WORK SCRIPT STARTED ===")
    print("\n🚀 SAVE WORK SCRIPT 🚀")
    print("======================")

    # Check if there are changes before proceeding
    changes = check_git_status()
    if not changes:
        logger.info("No changes detected, exiting")
        print("✅ No changes to commit. Exiting.")
        return
    
    file_count = len(changes.splitlines())
    print(f"📄 Found {file_count} changed file(s)")
    logger.info(f"Changes detected in {file_count} file(s)")
    
    # Ask if the user wants to enable safe mode
    safe_mode = input("🔒 Enable safe mode to check for sensitive info? (y/n): ").strip().lower() == 'y'
    if safe_mode:
        logger.info("Safe mode enabled - will check for sensitive information")
        global check_for_sensitive_info
    else:
        logger.info("Safe mode disabled - skipping sensitive information check")
        # Replace the function with a dummy that always returns True
        check_for_sensitive_info = lambda: True

    # Quick branch selection
    branch = quick_branch_choice()
    if not branch:
        logger.error("Branch selection failed, exiting script")
        print("❌ Branch selection failed. Exiting.")
        return

    logger.info(f"Selected branch: {branch}")

    # Git Operations
    if not stage_changes():
        logger.error("Failed to stage changes, exiting script")
        print("❌ Failed to stage changes. Exiting.")
        return
        
    if not commit_changes():
        logger.error("Failed to commit changes, exiting script")
        print("❌ Failed to commit changes. Exiting.")
        return
    
    # Only pull if we're on main (to avoid rebasing new branches)
    if branch == "main":
        logger.info("Working on main branch, pulling latest changes before pushing")
        if not pull_latest_changes(branch):
            logger.warning("Failed to pull latest changes, continuing with push anyway")
            print("⚠️ Warning: Failed to pull latest changes.")
    
    # Add option to skip push
    push_option = input("🚀 Push changes to remote repository? (y/n): ").strip().lower()
    if push_option != 'y':
        logger.info("User chose to skip pushing changes")
        print("✅ Changes committed locally but not pushed.")
        return
    
    if not push_changes(branch):
        logger.error("Failed to push changes, exiting script")
        print("❌ Failed to push changes. Exiting.")
        return

    logger.info("=== SAVE WORK SCRIPT COMPLETED SUCCESSFULLY ===")
    print(f"\n✅ SUCCESS! All changes pushed to '{branch}' 🎉")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"❌ Unexpected error: {str(e)}")
