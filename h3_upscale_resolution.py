class H3UpscaleResolution:
    """Choose an H3-safe upscale resolution from the original workflow size.

    The node is deliberately independent of the H3 sampler/upscaler. Feed the
    original width and height into it, then connect its width/height outputs to
    both MMH3 Latent Upscale with Model Params and MMH3 Spatial Split Params.
    """

    PRESETS = {
        "1280 x 720": (1280, 720),
        "1280 x 768": (1280, 768),
        "1344 x 768": (1344, 768),
        "1536 x 864": (1536, 864),
        "1600 x 896": (1600, 896),
        "1792 x 1024": (1792, 1024),
        "1920 x 1088 (H3)": (1920, 1088),
        "1920 x 1152": (1920, 1152),
        "2048 x 1152": (2048, 1152),
        "2304 x 1280": (2304, 1280),
        "2560 x 1440": (2560, 1440),
        "2688 x 1536": (2688, 1536),
        "3072 x 1728": (3072, 1728),
        "3200 x 1800": (3200, 1800),
        "3840 x 2160": (3840, 2160),
        "4096 x 2304": (4096, 2304),
    }

    SCALES = [
        "1.00x", "1.25x", "1.50x", "1.75x", "2.00x", "2.25x",
        "2.50x", "2.75x", "3.00x", "3.50x", "4.00x",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_width": ("INT", {"default": 1344, "min": 32, "max": 8192, "step": 32}),
                "input_height": ("INT", {"default": 768, "min": 32, "max": 8192, "step": 32}),
                "orientation": (["Auto", "Landscape", "Portrait"], {"default": "Auto"}),
                "mode": (["Common Resolution", "Scale", "Custom"], {"default": "Common Resolution"}),
                "resolution": (list(cls.PRESETS.keys()), {"default": "1920 x 1088 (H3)"}),
                "scale": (cls.SCALES, {"default": "2.00x"}),
                "custom_width": ("INT", {"default": 1920, "min": 32, "max": 8192, "step": 32}),
                "custom_height": ("INT", {"default": 1088, "min": 32, "max": 8192, "step": 32}),
                "rounding": (["Nearest", "Down", "Up"], {"default": "Nearest"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "report")
    FUNCTION = "calculate"
    CATEGORY = "H3/Utility"

    def _safe32(self, value, direction):
        value = max(32, int(round(value)))
        rem = value % 32
        if rem == 0:
            return value
        if direction == "Down":
            return max(32, value - rem)
        if direction == "Up":
            return value + (32 - rem)
        return value - rem if rem < 16 else value + (32 - rem)

    def _orient(self, w, h, orientation):
        if orientation == "Landscape" and w < h:
            return h, w
        if orientation == "Portrait" and w > h:
            return h, w
        return w, h

    def calculate(self, input_width, input_height, orientation, mode, resolution,
                  scale, custom_width, custom_height, rounding):
        iw = self._safe32(input_width, "Nearest")
        ih = self._safe32(input_height, "Nearest")
        input_landscape = iw >= ih

        if mode == "Common Resolution":
            w, h = self.PRESETS[resolution]
            w, h = self._orient(w, h, orientation)
        elif mode == "Scale":
            factor = float(scale.rstrip("x"))
            w = iw * factor
            h = ih * factor
            w = self._safe32(w, rounding)
            h = self._safe32(h, rounding)
            w, h = self._orient(w, h, orientation)
        else:
            w = self._safe32(custom_width, rounding)
            h = self._safe32(custom_height, rounding)
            w, h = self._orient(w, h, orientation)

        # Presets are already multiples of 32, but enforce it for future edits.
        w = self._safe32(w, rounding)
        h = self._safe32(h, rounding)

        in_ratio = iw / float(ih)
        out_ratio = w / float(h)
        scale_x = w / float(iw)
        scale_y = h / float(ih)

        report = (
            f"H3 Upscale Resolution\n"
            f"Input:  {iw} x {ih}\n"
            f"Output: {w} x {h}\n"
            f"Mode:   {mode}\n"
            f"Orientation: {orientation}\n"
            f"Scale:  {scale_x:.3f}x width / {scale_y:.3f}x height\n"
            f"Aspect: {in_ratio:.4f} -> {out_ratio:.4f}\n"
            f"H3 alignment: {w % 32 == 0 and h % 32 == 0} (multiple of 32)"
        )
        print("[H3UpscaleResolution] " + report.replace("\n", " | "), flush=True)
        return (int(w), int(h), report)


NODE_CLASS_MAPPINGS = {
    "H3UpscaleResolution": H3UpscaleResolution,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3UpscaleResolution": "H3 Upscale Resolution",
}
