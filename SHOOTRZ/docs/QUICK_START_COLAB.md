# Quick Start: Training Models in Google Colab

This is a step-by-step guide to train your first model in Google Colab.

## Step-by-Step Instructions

### Step 1: Prepare Your Dataset

1. **Convert DeepSport to YOLO format** (if not done already):
   ```bash
   cd SHOOTRZ
   python scripts/convert_deepsport_to_yolo.py --deepsport-path data/ball/deepsport --output-path data/ball/deepsport_yolo
   ```

2. **Create zip file for upload**:
   ```bash
   cd data/ball
   zip -r deepsport_yolo.zip deepsport_yolo/
   ```

### Step 2: Upload Dataset to Google Drive

1. Go to [Google Drive](https://drive.google.com/)
2. Create a new folder called `SHOOTRZ_Datasets`
3. Upload `deepsport_yolo.zip` to this folder

### Step 3: Open Google Colab

1. Go to [Google Colab](https://colab.research.google.com/)
2. Sign in with your Google account

### Step 4: Upload the Training Notebook

**Option A: Upload from your computer**
1. In Colab, click `File` → `Upload notebook`
2. Navigate to `SHOOTRZ/notebooks/train_yolov8_ball_colab.ipynb`
3. Click `Upload`

**Option B: Create new notebook and copy cells**
1. In Colab, click `File` → `New notebook`
2. Copy each cell from `train_yolov8_ball_colab.ipynb` into the new notebook

### Step 5: Enable GPU

1. In Colab, click `Runtime` → `Change runtime type`
2. Under `Hardware accelerator`, select `GPU`
3. Choose `T4` or `V100` if available (free tier usually gets T4)
4. Click `Save`

### Step 6: Run the Notebook

1. **Run the first cell** (GPU check):
   - Click on the first code cell
   - Press `Shift + Enter` or click the play button
   - You should see: `CUDA available: True` and your GPU name

2. **Run the second cell** (Install dependencies):
   - This installs `ultralytics` package
   - Wait for installation to complete

3. **Run the third cell** (Mount Drive):
   - This will ask for authorization
   - Click the link, authorize access, copy the authorization code
   - Paste it into the text box and press Enter
   - You should see: `Mounted at /content/drive`

4. **Run the fourth cell** (Load Dataset):
   - This extracts your dataset from Google Drive
   - Wait for extraction to complete
   - You should see the dataset structure listed

5. **Run the fifth cell** (Training Configuration):
   - This sets up training parameters
   - Review the configuration (you can modify if needed)

6. **Run the sixth cell** (Start Training):
   - ⚠️ **This will take 1-3 hours depending on dataset size**
   - You'll see training progress with loss values
   - The model will save checkpoints every 10 epochs

7. **Run the seventh cell** (Validation):
   - This tests the trained model on the test set
   - You'll see mAP (mean Average Precision) scores

8. **Run the eighth cell** (Save to Drive):
   - This saves the best model to Google Drive
   - You can access it later from Drive

9. **Run the ninth cell** (Download Model):
   - This downloads the model to your computer
   - The `.pt` file will be saved to your Downloads folder

### Step 7: Use Your Trained Model

1. **Copy the downloaded model** to your project:
   ```bash
   # Move the downloaded file to your models directory
   mv ~/Downloads/yolov8n_basketball_deepsport.pt SHOOTRZ/models/
   ```

2. **Test the model**:
   ```bash
   cd SHOOTRZ
   python scripts/comprehensive_evaluation.py --deepsport-path data/ball/deepsport
   ```

3. **The model will be automatically detected** by the pipeline when you run analysis!

## Troubleshooting

### "Dataset zip not found"
- Make sure you uploaded `deepsport_yolo.zip` to `SHOOTRZ_Datasets/` folder in Drive
- Check the folder name matches exactly (case-sensitive)

### "CUDA out of memory"
- Reduce batch size in config: change `'batch': 32` to `'batch': 16` or `'batch': 8`
- Reduce image size: change `'imgsz': 640` to `'imgsz': 416`

### "Session disconnected"
- Colab free tier has time limits
- Save checkpoints to Drive frequently (cell 8)
- Resume training from last checkpoint if needed

### "Training is too slow"
- Make sure GPU is enabled (Step 5)
- Check GPU usage: `Runtime` → `Manage sessions` → View GPU usage
- Free tier GPUs can be slower during peak hours

## Next Steps

After training the ball detection model:

1. **Train YOLOv8-pose** for pose estimation:
   - Use `train_yolov8_pose_colab.ipynb` (create it similar to ball detection)
   - Dataset: `basketball_pose_yolo.zip` (created with `create_pose_dataset.py`)

2. **Train 3D lifting models** (optional, requires 3D datasets):
   - PoseMagic or HybrIK models
   - Requires Human3.6M or CMU MoCap datasets

3. **Evaluate all models**:
   ```bash
   python scripts/comprehensive_evaluation.py
   ```

## Tips

- **Save frequently**: Run the "Save to Drive" cell every 20-30 epochs
- **Monitor training**: Watch the loss values - they should decrease over time
- **Early stopping**: The model uses `patience=20` - training stops if no improvement for 20 epochs
- **Best model**: The `best.pt` file is automatically saved - this is the one to use!

## Need Help?

- Check [COLAB_TRAINING_GUIDE.md](./COLAB_TRAINING_GUIDE.md) for detailed information
- Review training logs in Colab output
- Check model performance on validation set before downloading

