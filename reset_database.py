# reset.py
import os
import shutil

def reset_app():
    """Reset the application data"""
    print("Resetting Smart Study AI...")
    
    # Delete database
    if os.path.exists("data/study_ai.db"):
        os.remove("data/study_ai.db")
        print("✓ Database deleted")
    
    # Delete uploads
    if os.path.exists("data/uploads"):
        shutil.rmtree("data/uploads")
        print("✓ Uploads deleted")
    
    # Recreate directories
    os.makedirs("data/uploads", exist_ok=True)
    print("✓ Directories recreated")
    
    print("\n✅ Reset complete! You can now run: streamlit run main.py")

if __name__ == "__main__":
    reset_app()