from PIL import Image
import os

def create_favicon(image_path, output_path='favicon.ico', sizes=[16, 32, 48, 64, 128, 256]):
    """
    Convert a PNG or JPEG image to a multi-size favicon ICO file.
    
    Parameters:
    image_path (str): Path to the source image (PNG or JPEG)
    output_path (str): Path where the favicon will be saved (default: 'favicon.ico')
    sizes (list): List of icon sizes to include (default: [16, 32, 48, 64, 128, 256])
    """
    # Check if file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Could not find image file: {image_path}")
    
    # Check file extension
    valid_extensions = ['.png', '.jpg', '.jpeg']
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext not in valid_extensions:
        raise ValueError(f"Unsupported file format. Please use: {', '.join(valid_extensions)}")
        
    # Open image
    img = Image.open(image_path)
    
    # Convert to RGBA to preserve transparency for PNGs
    # For JPEGs this ensures consistent color handling
    img = img.convert('RGBA')
    
    # If the image is not square, crop it to a square from the center
    if img.width != img.height:
        min_dimension = min(img.width, img.height)
        left = (img.width - min_dimension) // 2
        top = (img.height - min_dimension) // 2
        right = left + min_dimension
        bottom = top + min_dimension
        img = img.crop((left, top, right, bottom))
    
    # Create a list to store different size versions
    icons = []
    
    # Create each size and append to icons list
    for size in sizes:
        # Resize the image with antialiasing
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(resized)
    
    try:
        # Save the favicon file
        icons[0].save(
            output_path,
            format='ICO',
            sizes=[(i.width, i.height) for i in icons],
            append_images=icons[1:]
        )
        print(f"Successfully created favicon at: {output_path}")
    except Exception as e:
        raise Exception(f"Error saving favicon: {str(e)}")
    
    return output_path

# Example usage
if __name__ == "__main__":
    # Works with both PNG and JPEG files
    create_favicon('./static/logo.png', './static/favicon.ico')