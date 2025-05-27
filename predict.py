import os
from PIL import Image, ImageDraw
import numpy as np
from cog import BasePredictor, Input, Path
import io


class Predictor(BasePredictor):
    def predict(
        self,
        image: Path = Input(description="Input image to convert to dot grid"),
        grid_size: int = Input(
            description="Size of each dot in the grid (higher = fewer, larger dots)",
            default=8,
            ge=2,
            le=50
        ),
        dot_scale: float = Input(
            description="Scale factor for dot size relative to grid cell (0.1-1.0)",
            default=0.8,
            ge=0.1,
            le=1.0
        ),
        output_width: int = Input(
            description="Width of output image in pixels",
            default=1024,
            ge=256,
            le=2048
        ),
        brightness_threshold: float = Input(
            description="Brightness threshold for dot visibility (0.0-1.0)",
            default=0.1,
            ge=0.0,
            le=1.0
        )
    ) -> Path:
        """
        Convert an image into a vectorized dot grid with circular dots on black background
        """
        
        # Load and process input image
        img = Image.open(image).convert('RGB')
        
        # Calculate output dimensions maintaining aspect ratio
        aspect_ratio = img.height / img.width
        output_height = int(output_width * aspect_ratio)
        
        # Calculate grid dimensions
        grid_width = output_width // grid_size
        grid_height = output_height // grid_size
        
        # Resize image to match grid resolution
        img_resized = img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
        img_array = np.array(img_resized)
        
        # Create output image with black background
        output_img = Image.new('RGB', (output_width, output_height), color='black')
        draw = ImageDraw.Draw(output_img)
        
        # Calculate dot radius (constant size for all dots)
        dot_radius = (grid_size * dot_scale) / 2
        
        # Process each pixel in the grid
        for y in range(grid_height):
            for x in range(grid_width):
                # Get pixel color
                pixel_color = img_array[y, x]
                
                # Calculate brightness (luminance)
                brightness = (0.299 * pixel_color[0] + 
                            0.587 * pixel_color[1] + 
                            0.114 * pixel_color[2]) / 255.0
                
                # Skip very dark pixels based on threshold
                if brightness < brightness_threshold:
                    continue
                
                # Calculate dot position (center of grid cell)
                dot_x = x * grid_size + grid_size // 2
                dot_y = y * grid_size + grid_size // 2
                
                # All dots use the same maximum size
                left = dot_x - dot_radius
                top = dot_y - dot_radius
                right = dot_x + dot_radius
                bottom = dot_y + dot_radius
                
                color = tuple(pixel_color.astype(int))
                draw.ellipse([left, top, right, bottom], fill=color)
        
        # Save output image
        output_path = "/tmp/dot_grid_output.png"
        output_img.save(output_path, "PNG", quality=95)
        
        return Path(output_path)


# Alternative version with more control over dot appearance
class AdvancedPredictor(BasePredictor):
    def predict(
        self,
        image: Path = Input(description="Input image to convert to dot grid"),
        grid_size: int = Input(
            description="Size of each dot in the grid",
            default=10,
            ge=3,
            le=50
        ),
        dot_scale: float = Input(
            description="Scale factor for dot size",
            default=0.9,
            ge=0.1,
            le=1.0
        ),
        output_size: int = Input(
            description="Output image size (will be square)",
            default=1024,
            ge=512,
            le=2048
        ),
        color_mode: str = Input(
            description="Color mode for dots",
            choices=["original", "grayscale", "high_contrast"],
            default="original"
        ),
        background_color: str = Input(
            description="Background color",
            choices=["black", "white", "dark_gray"],
            default="black"
        ),
        dot_spacing: float = Input(
            description="Spacing between dots (1.0 = touching)",
            default=1.0,
            ge=0.5,
            le=2.0
        )
    ) -> Path:
        """
        Advanced dot grid converter with more customization options
        """
        
        # Load image
        img = Image.open(image).convert('RGB')
        
        # Make image square by cropping to center
        min_dim = min(img.width, img.height)
        left = (img.width - min_dim) // 2
        top = (img.height - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        
        # Calculate grid parameters
        dots_per_side = output_size // grid_size
        actual_grid_size = grid_size * dot_spacing
        
        # Resize image to match dot grid resolution
        img_resized = img.resize((dots_per_side, dots_per_side), Image.Resampling.LANCZOS)
        
        # Set background color
        bg_colors = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "dark_gray": (32, 32, 32)
        }
        bg_color = bg_colors[background_color]
        
        # Create output image
        output_img = Image.new('RGB', (output_size, output_size), color=bg_color)
        draw = ImageDraw.Draw(output_img)
        
        # Convert to numpy for processing
        img_array = np.array(img_resized)
        
        # Calculate dot radius (constant size for all dots)
        base_radius = (grid_size * dot_scale) / 2
        
        # Process each dot
        for y in range(dots_per_side):
            for x in range(dots_per_side):
                pixel_color = img_array[y, x]
                
                # Calculate brightness
                brightness = np.mean(pixel_color) / 255.0
                
                # Skip very dark pixels for black backgrounds
                if background_color == "black" and brightness < 0.05:
                    continue
                    
                # Skip very bright pixels for white backgrounds
                if background_color == "white" and brightness > 0.95:
                    continue
                
                # Determine dot color based on mode
                if color_mode == "original":
                    dot_color = tuple(pixel_color.astype(int))
                elif color_mode == "grayscale":
                    gray_val = int(brightness * 255)
                    dot_color = (gray_val, gray_val, gray_val)
                else:  # high_contrast
                    if brightness > 0.5:
                        dot_color = (255, 255, 255)
                    else:
                        dot_color = (0, 0, 0)
                
                # Calculate dot position
                center_x = x * actual_grid_size + actual_grid_size // 2
                center_y = y * actual_grid_size + actual_grid_size // 2
                
                # All dots use the same maximum size
                radius = base_radius
                
                # Draw dot
                left = center_x - radius
                top = center_y - radius
                right = center_x + radius
                bottom = center_y + radius
                
                draw.ellipse([left, top, right, bottom], fill=dot_color)
        
        # Save output
        output_path = "/tmp/advanced_dot_grid.png"
        output_img.save(output_path, "PNG", quality=95)
        
        return Path(output_path)
