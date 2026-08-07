ComfyUI Detailer/ADetailer Workflow
===================================

Requirements for each version are listed below or can be found inside a **Note** in the Workflow itself.

Because of the many connections among the nodes, I **highly** recommend turning off the link visibility by clicking the **"Toggle Link visibility"** (Eye icon) in the bottom right of ComfyUI.

[![](https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/ff81b9c8-74d4-44e5-9380-72d250195779/width=525/ff81b9c8-74d4-44e5-9380-72d250195779.jpeg)](https://civitai.com/articles/15480)

Description
-----------

I originally came from A1111 WebUI to ComfyUI and, honestly, a lot of things felt way more complicated than they needed to be. I couldn’t find workflows that were both visually pleasing _and_ showed me all the important options without requiring a deep understanding of every little thing in ComfyUI.

Over a few months I learned the ins and outs of Comfy and built my own very barebones, simple workflow (v1) with one main goal: streamline the process and make it visually understandable. I released it here thinking it might help others who also want to make the jump from A1111 to Comfy.

Over the last year I’ve kept adding more and more features as people started using the workflow and requesting things. The workflow has grown a lot, but I’m still trying to keep the same ease-of-use that this whole journey started with. The main goal is still the same: give you a lot of powerful options in a layout that’s as clean, readable, and as user-friendly as ComfyUI will allow.

At this point I feel like I have a pretty solid understanding of how Comfy works, and I’ve even created my own custom nodes to add missing functionality so this workflow could match the ideas I had for it. I try to hide as much of the technical complexity as possible — but if you’re ever curious or confused about anything, please feel free to ask!

Thanks to all of your suggestions, the workflow now includes features like:

*   Single-image and batch generation
    
*   Automatic detailers for specific body parts
    
*   Upscaling
    
*   v-pred models
    
*   LoRAs
    
*   ControlNet
    
*   IPAdapter
    
*   Hires fix / refiner
    
*   Manual inpainting
    

Thank you to every single person who uses this workflow, donates Buzz, or shares images on this page.  
I really appreciate you taking those extra steps to support and promote the project. ♥️

Requirements
------------

**v4.4 and above require ComfyUI version 0.3.51 or above and also need the** [**frontend**](https://github.com/Comfy-Org/ComfyUI_frontend?tab=readme-ov-file#nightly-releases) **to be AT LEAST 1.24.3 or later.**

### **v5.0** \- Full List

*   [ComfyUI Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
    
*   [ComfyUI Impact Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
    
*   [ComfyUI-mxToolkit](https://github.com/Smirnov75/ComfyUI-mxToolkit)
    
*   [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
    
*   [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
    
*   [ComfyUI-Crystools](https://github.com/crystian/ComfyUI-Crystools)
    
*   [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver)
    
*   [ComfyUI\_Comfyroll\_CustomNodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes)
    
*   [ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)
    
*   [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
    
*   [ComfyUI\_IPAdapter\_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
    
*   [ComfyUI-vslinx-nodes](https://github.com/vslinx/ComfyUI-vslinx-nodes)
    
*   [ComfyUI-Inpaint-CropAndStitch](https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch)
    
*   [comfyui\_controlnet\_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
    
*   [cg-image-filter](https://github.com/chrisgoringe/cg-image-filter)
    
*   [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
    
*   [wlsh\_nodes](https://github.com/wallish77/wlsh_nodes)
    

### **v4.4** \- Additions to v4.3 **(IMG2IMG Only)**

*   [ComfyUI-vslinx-nodes](https://github.com/vslinx/ComfyUI-vslinx-nodes)
    
*   Otherwise same as **v4-4.3** below
    

### **v4.2-4.3** \- Additions to v4.1

*   [WLSH Nodes](https://github.com/wallish77/wlsh_nodes)
    
*   Otherwise same as **v4.1** (incl. **v4**) below
    

### v4.1 - Additions to v4 (IMG2IMG Only)

*   [ComfyUI-WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger)
    
*   Otherwise same as **v4** below
    

### v4 - Full List

*   [ComfyUI Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
    
*   [ComfyUI Impact Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
    
*   [ComfyUI-mxToolkit](https://github.com/Smirnov75/ComfyUI-mxToolkit)
    
*   [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
    
*   [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
    
*   [ComfyUI-Crystools](https://github.com/crystian/ComfyUI-Crystools)
    
*   [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver)
    
*   [ComfyUI\_Comfyroll\_CustomNodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes)
    
*   [ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)
    
*   [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
    
*   [ComfyUI\_IPAdapter\_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
    
*   [comfyui\_controlnet\_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
    
*   [cg-use-everywhere](https://github.com/chrisgoringe/cg-use-everywhere)
    
*   [cg-image-filter](https://github.com/chrisgoringe/cg-image-filter)
    
*   [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
    

### v3 - v3.2 - Full List

*   [ComfyUI Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
    
*   [ComfyUI Impact Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
    
*   [ComfyUI-mxToolkit](https://github.com/Smirnov75/ComfyUI-mxToolkit)
    
*   [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
    
*   [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
    
*   [ComfyUI-Crystools](https://github.com/crystian/ComfyUI-Crystools)
    
*   [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver)
    
*   [ComfyUI\_Comfyroll\_CustomNodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes)
    
*   [ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)
    
*   [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
    
*   [comfyui\_controlnet\_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
    
*   [cg-use-everywhere](https://github.com/chrisgoringe/cg-use-everywhere)
    
*   [cg-image-filter](https://github.com/chrisgoringe/cg-image-filter)
    
*   [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
    

### v2.2 - Additions to v2

*   [ComfyUI\_Comfyroll\_Nodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes)
    
*   Otherwise same Custom-Nodes as v2 but you can remove [Comfyui-ergouzi-Nodes](https://github.com/11dogzi/Comfyui-ergouzi-Nodes)
    

v2 - Full List
--------------

*   [ComfyUI Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
    
*   [ComfyUI Impact Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
    
*   [ComfyUI-mxToolkit](https://github.com/Smirnov75/ComfyUI-mxToolkit)
    
*   [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
    
*   [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
    
*   [ComfyUI-Crystools](https://github.com/crystian/ComfyUI-Crystools)
    
*   [Comfyui-ergouzi-Nodes](https://github.com/11dogzi/Comfyui-ergouzi-Nodes)
    
*   [ComfyUI-Image-Saver](https://github.com/alexopus/ComfyUI-Image-Saver)
    
*   [cg-use-everywhere](https://github.com/chrisgoringe/cg-use-everywhere)
    
*   [cg-image-filter](https://github.com/chrisgoringe/cg-image-filter)
    
*   [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)
    

v1 - Full List
--------------

*   [ComfyUI Impact Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
    
*   [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
    
*   [cg-use-everywhere](https://github.com/chrisgoringe/cg-use-everywhere)
    
*   [cg-image-picker](https://github.com/chrisgoringe/cg-image-picker)
    
*   [ComfyUI Impact Subpack](https://github.com/ltdrdata/ComfyUI-Impact-Subpack)
    

How to use
----------

Since all of the different versions work differently, you should check the **"How to use"** Node inside of the Workflow itself.

I promise that once you read the explanation of the workflow itself, it'll click and it will be a simple plug and play experience.

It's the simplest I could've made it coming from someone who's only started using ComfyUI 4-5 months ago and had been exclusively an A1111WebUI user before.

When were what functionalitys added?
------------------------------------

Starting from **v3**, ControlNet is included.  
Starting from **v4**, IPAdapter is included.  
Starting from **v4.3**, HiRes Fix and Dynamic prompts(wildcards) is included.  
Starting from **v4.4**, Refiner is included.  
Starting from **v5.0**, Manual Inpainting is included.

Any errors during execution?
----------------------------

If you're running into any errors during the execution of the workflow, please check the [FAQ of my Guide](https://civitai.com/articles/15480#faq:) first. The guide is written for the IMG2IMG Workflow but when issues arise that people run into frequently i'll add the solutions and what's hapenning to that FAQ section.  
If you can't find the problem you're running into there - feel free to write me a comment **and include your logs from your comfyui console that show the error** on the model page so that i can help you and other people might benefit from it as well.

Feedback
--------

I'd love to see your feedback or opinion on the workflow.  
This is the first workflow I have ever created myself from scratch and I'd love to hear what you think of it.

If you want to do me a huge favor, you can post your results on this Model page.  
I'll make sure to send some buzz your way!