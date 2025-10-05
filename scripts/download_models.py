"""
Download Whisper models to local directory.

Usage:
    python scripts/download_models.py --model base
    python scripts/download_models.py --model base --model small
    python scripts/download_models.py --all
"""

import argparse
import sys
from pathlib import Path
from faster_whisper import WhisperModel


AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "large-v3"]

MODEL_INFO = {
    "tiny": {"size": "75 MB", "description": "Fastest, basic accuracy"},
    "base": {"size": "142 MB", "description": "Good balance of speed and accuracy"},
    "small": {"size": "466 MB", "description": "Better accuracy, slower"},
    "medium": {"size": "1.5 GB", "description": "High accuracy"},
    "large": {"size": "2.9 GB", "description": "Best accuracy, multilingual"},
    "large-v3": {"size": "2.9 GB", "description": "Latest large model"},
}


def download_model(model_name: str, model_dir: str, device: str = "cpu", compute_type: str = "int8"):
    """
    Download a Whisper model.
    
    Args:
        model_name: Name of the model to download
        model_dir: Directory to save the model
        device: Device type (cpu or cuda)
        compute_type: Computation type
    """
    print(f"\n{'='*60}")
    print(f"Downloading model: {model_name}")
    print(f"Size: {MODEL_INFO[model_name]['size']}")
    print(f"Description: {MODEL_INFO[model_name]['description']}")
    print(f"Directory: {model_dir}")
    print(f"{'='*60}\n")
    
    try:
        # Loading the model will automatically download it
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root=model_dir
        )
        
        print(f"✓ Successfully downloaded {model_name}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download {model_name}: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Download Whisper models for transcription service"
    )
    parser.add_argument(
        "--model",
        action="append",
        choices=AVAILABLE_MODELS,
        help="Model to download (can be specified multiple times)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available models"
    )
    parser.add_argument(
        "--model-dir",
        default="./models",
        help="Directory to save models (default: ./models)"
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device type for model validation"
    )
    parser.add_argument(
        "--compute-type",
        choices=["int8", "float16", "float32"],
        default="int8",
        help="Computation type"
    )
    
    args = parser.parse_args()
    
    # Determine which models to download
    if args.all:
        models_to_download = AVAILABLE_MODELS
    elif args.model:
        models_to_download = args.model
    else:
        parser.print_help()
        print("\nError: Please specify --model or --all")
        sys.exit(1)
    
    # Create model directory
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting download of {len(models_to_download)} model(s)...")
    print(f"Target directory: {model_dir.absolute()}\n")
    
    # Download models
    results = {}
    for model_name in models_to_download:
        results[model_name] = download_model(
            model_name,
            str(model_dir),
            args.device,
            args.compute_type
        )
    
    # Print summary
    print(f"\n{'='*60}")
    print("Download Summary:")
    print(f"{'='*60}")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for model_name, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {model_name:12} - {status}")
    
    print(f"\nTotal: {success_count}/{total_count} models downloaded successfully")
    
    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()