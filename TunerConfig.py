from core.constants import Tags, SaveStyle
import os
import copy

class TunerConfig():
# Change these if you have specific
    # samples you like to work with
    img_sample_color = "./tuner_sample_color.png"
    img_sample_bw = "./tuner_sample_bw.jpg"

    output_dir = "./wip"
    # why bother looking at uninteresting stuff, and let's preserve old runs
    save_style = SaveStyle.tagged | SaveStyle.overwrite

    def __init__(self) -> None:
        # sort out where we will save results, defaulting to cwd
        self.wip_dir = "." if (TunerConfig.output_dir is None or TunerConfig.output_dir == "") else os.path.realpath(TunerConfig.output_dir)
        if not os.path.exists(self.wip_dir): self.wip_dir = "."
        self.wip_dir = os.path.realpath(self.wip_dir)

        self.save_all = False if (TunerConfig.save_style & SaveStyle.tagged == SaveStyle.tagged) else True
        self.overwrite_file = True if (TunerConfig.save_style & SaveStyle.overwrite == SaveStyle.overwrite) else False
        # used by the carousel context
        self.tag_codes = [i.value for i in Tags]
        self.tag_names = [i.name for i in Tags]

        # used when saving args
        self.tag_map = {}
        for tag in self.tag_names:
            self.tag_map[tag] = False

        return

    @property
    def default_tag_map(self):
        return copy.deepcopy(self.tag_map)