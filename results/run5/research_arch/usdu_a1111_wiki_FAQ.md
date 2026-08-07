# How it works
Enlarges the image with the selected upscaler, then divides the image into tiles and inpaints it. If the "Seams fix" option is set, then it additionally goes along the seams and redraws them.
***

# Parameters descriptions
* **Denoise** - uses from default img2img field. We recommend 0.35 value for image enhancements, but if you don't wan't changes use 0.15-0.20
* **Target size type** - Where to get the size of the final image
  * **From img2img settings** - Default img2img width and height sliders
  * **Custom size** - Built in width and height sliders. Max values - 8192
  * **Scale from image size** - Init image size multiplied by scale factor
* **Redraw**
  * **Upscaler** - upscale image before redrawing. Use what you like. Our recommendation - ESRGAN to photorealistic images, R-ESRGAN 4x+ for others (less requirements)
  * **Type**
    * **Linear** - All tiles processed one by one. column by column, row by row
    * **Chess** - All tiles are processed in a checkerboard pattern. Reduces the chance of seam artifacts
    * **None** - Disabled redraw. Use it when run generation without seam fix, see visible overlays or artifacts on seams and want to run just seam pass. Don't forget to put upscaled image as the source before
  * **Tile width** - The width of the tile to be processed. The larger the tile, the less artifacts will be in the final image. For 2k 512px is usually enough
  * **Tile height** - The height of the tile to be processed. The default is 0, in which case it is equal to the width. The larger the tile, the less artifacts will be in the final image. For 2k 512px is usually enough
  * **Padding** - How many pixels of neighboring tiles will be taken into account when processing a tile
  * **Mask blur** - It is blur of masks used in tile masking. Set it to 12-16 on 512-768px tile size. Increase if you see seams.
* **Seams fix** - Do not use it if result image haven't visible grid, it's just another redraw passes.
  * **Type**
    * **Bands pass** - It adds passes on just seams (rows and columns) and covers small area around them (width in ui). It requires less time than offset pass.
    * **Half tile offset pass** - It adds 2 passes like redraw pass, but with a half-tile offset. One pass for rows with vertical gradient mask and one pass for columns with horizontal gradient mask. This pass covers bigger area than bands and mostly produces better result, but require more time.
    * **Half tile offset + intersections pass** - It runs Half tile offset pass and then run extra pass on intersections with radial gradient mask
    * **None** - Disabled seams fix. Default value
  * **Denoise** - Denoise strength for seams fix
  * **Width** - Redraw line width. Used only by "Band pass"
  * **Padding** - How many pixels of image near seam will be taken into account when processing a tile
  * **Mask blur** - It is blur of masks used in tile masking. Set it to 8-16 on 32px padding. Increase if increased padding.
* **Save options**
  * **Upscaled** - Enabled by default. Saving image from **Redraw**
  * **Seams fix** - Disabled by default. Saving image after **Seams fix**

Jopezzia's default settings:

![1-ui](https://user-images.githubusercontent.com/17219767/212113796-63267256-823e-4b4c-822c-b89f19c24bb2.png)
![2-ui](https://user-images.githubusercontent.com/17219767/212113809-67bbbda1-ab97-4f15-ad9b-bdb1bb5112ac.png)

# How to use with ControlNet
Here is an example from the channel [ Sebastian Kamph](https://www.youtube.com/@sebastiankamph)

[![4-controlnetexample](http://img.youtube.com/vi/EmA0RwWv-os/0.jpg)](http://www.youtube.com/watch?v=EmA0RwWv-os)

# I have AttributeError: module 'modules.images' has no attribute 'flatten' error
Update your automatic1111 web-ui. At least to this commit https://github.com/AUTOMATIC1111/stable-diffusion-webui/commit/9441c28c947588d756e279a8cd5db6c0b4a8d2e4

# I have something like RuntimeError: Given groups=1, weight of size [64, 3, 3, 3], expected input[1, 4, 256, 256] to have 3 channels, but got 4 channels instead error
Try to set upscaler for img2img to none
![3-img2img-upscale-none](https://user-images.githubusercontent.com/11600962/211805882-3f1334b8-18f1-4fd5-ab2c-27bd9d552ffd.png)
If that didn't help try to disable "Apply color correction to img2img results to match original colors" in settings.