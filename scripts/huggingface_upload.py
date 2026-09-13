import os
from huggingface_hub import HfApi

# Ensure you have logged in using `huggingface-cli login` or set the HF_TOKEN environment variable.

repo_id = "callensxavier/OpenAI-NSE-Thermodynamic-Censorship"
api = HfApi()

print(f"Uploading files to HuggingFace dataset: {repo_id}")

try:
    # Upload directive outputs
    outputs_dir = os.path.join("scripts", "directive_outputs")
    if os.path.exists(outputs_dir):
        api.upload_folder(
            folder_path=outputs_dir,
            repo_id=repo_id,
            path_in_repo="directive_outputs",
            repo_type="dataset"
        )
        print("Successfully uploaded directive_outputs.")
    
    # Upload certificates
    cert_file = "openai_lean_audit_certificate.json"
    if os.path.exists(cert_file):
        api.upload_file(
            path_or_fileobj=cert_file,
            path_in_repo=cert_file,
            repo_id=repo_id,
            repo_type="dataset"
        )
        print("Successfully uploaded audit certificate.")

    # Upload animations/images if available
    anim_dir = os.path.join("dataset", "animations")
    if os.path.exists(anim_dir):
        api.upload_folder(
            folder_path=anim_dir,
            repo_id=repo_id,
            path_in_repo="animations",
            repo_type="dataset"
        )
        print("Successfully uploaded animations.")

    print("\nHuggingFace dataset successfully updated!")

except Exception as e:
    print(f"Error during upload: {e}")
    print("\nPlease ensure you are authenticated. Run 'huggingface-cli login' in your terminal.")
