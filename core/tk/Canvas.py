import tkinter as tk
from tkinter import ttk

from cvxopt import matrix, solvers
import numpy as np
import cv2
# import PIL
from PIL import Image, ImageTk



class Canvas():
    def __init__(self,master, status_panel) -> None:
        # assume there is just the one pic for now
        self.canvas:tk.Canvas = tk.Canvas(master=master
                ,background="black",relief=tk.FLAT
                ,border=2)
        self.canvas.grid(in_=master,column=0,row=0,sticky="nswe")
        self.canvas.bind('<Configure>',self.on_canvas_resized)
        self.resiz=""
        self.images = {}
        self.status_panel = status_panel
        self.master = master
        solvers.options['show_progress'] = False
        return
    def on_canvas_resized(self, e, *args, **kwargs):
        self.__do_pil_pipeline()

        return

    def render(self, key,image):
        this = self.images[key] = {}
        this["cvImage"] = image
        self.__do_pil_pipeline()
        return

    def __do_pil_pipeline(self):
        '''
        maximize: height and width (c matrix)
        subject to: (A matrix)
            h>0
            w>0
            express proportion between two (e.g., w - 1.5w = 0)
            max width
            max height
        '''
        def get_A(iw,ih,sw,sh):
            if sh >= sw:
                if ih >= iw:
                    A =matrix( [
                        [1.0,0.0,-1.0,0.0,ih/iw] #ih/iw comes here for portrait, portrait
                        ,[0.0,1.0,0.0,-1.0, -1]
                    ])
                else:
                    A =matrix( [
                        [1.0,0.0,-1.0,0.0,-1]
                        ,[0.0,1.0,0.0,-1.0, iw/ih] #iw/ih comes here for portrait, landscape
                    ])
            else:
                if ih < iw:
                    A =matrix( [
                        [1.0,0.0,-1.0,0.0,-1]
                        ,[0.0,1.0,0.0,-1.0, iw/ih] #iw/ih comes here for landscape, portrait
                    ])
                else:
                    A =matrix( [
                        [1.0,0.0,-1.0,0.0,ih/iw] #ih/iw comes here for landscape,landscap
                        ,[0.0,1.0,0.0,-1.0, -1]
                    ])
            return A

        separator = 5
        num_images = len(self.images)
        if num_images == 0: return

        # maximizing height and width - mul by -1 since the optimizer is a cost minimizer
        c = matrix([1.0,1.0]) * -1

        tsh = self.master.winfo_height()
        tsw = self.master.winfo_width()
        sw = sh = 0
        if tsw >= tsh:
            # screen wider than it is tall - split horizontal panes (l,r)

            # this is how much space each image gets to display itself
            sw = (tsw - (separator * (num_images - 1)))/num_images
            sh = tsh
            for i,k in enumerate(self.images):
                this = self.images[k]
                top = 0
                left = (i * sw ) + (i * separator)
                this["tl"] = (left,top)
        else:
            # screen taller than it is wide - split vertical panes (t,b)
            sw = tsw
            sh = (tsh - (separator * (num_images - 1)))/num_images
            for i,k in enumerate(self.images):
                this = self.images[k]
                left = 0
                top = (i * sh ) + (i * separator)
                this["tl"] = (left,top)

        for k in self.images:
            this = self.images[k]
            image = np.copy(this["cvImage"])
            w = image.shape[1]
            h = image.shape[0]
            # A
            A = get_A(w,h,sw,sh)
            # b for this image
            b =matrix([float(sw),float(sh),0.0,0.0,0.0])

            # get resize dimensions
            sol=solvers.lp(c,A,b)
            # solver generally returns less than the max by one
            nw = int(sol['x'][0]) + 1
            nh = int(sol['x'][1]) + 1
            self.resize_mode = "SAMPL" if nw <= w else "INTER"
            if self.status_panel is not None: self.status_panel = self.resize_mode

            # use cv to resize
            image = cv2.resize(image
                                ,dsize=(nw,nh)
                                ,interpolation= cv2.INTER_AREA if nw <= w else cv2.INTER_LINEAR
                            )

            image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            # weird bug with the photo losing scope - hold a ref here
            this["photo_ref"] = ImageTk.PhotoImage(image=image)
            # phew, finally show
            x = ((sw - nw) // 2) + this["tl"][0]
            y = ((sh - nh) // 2) + this["tl"][1]
            self.canvas.create_image((x,y),image=this["photo_ref"],anchor="nw")

    def simple_resize(self, iw, ih, sw, sh):
        w = False
        h = False
        fx = None
        fy = None
        if sw > sh:
            # screen wider than it is tall
            # w=True
            if iw > ih:
                # and the image is wider
                # reshape to a width aspect ration
                w=True
                fy = fx = sw/iw
            else:
                # image is taller
                # reshape to a height aspect ratio
                h = True
                fy = fx = min(sw/iw, sh/ih)
        else:
            # screen taller than it is wide
            # h = True
            if ih > iw:
                # and the image is taller than it is wide
                # reshape to a height aspect ratio
                h = True
                fx = fy = sh/ih
            else:
                # image is wider
                # reshape to a width aspect ration
                w=True
                fy = fx = min(sw/iw, sh/ih)
        # if h:
        #     # we are reshaping to fy
        #     fx = fy = sh/ih
        #     # fx = (iw/ih) * fy
        # else:
        #     # we are reshaping fx
        #     fy = fx = sw/iw
        #     # fy = (sh/ih) * fx


        # random, huh?
        fx *= 1.2
        fy *= 1.2

        return fx,fy

    def demo_better_resize(self, iw, ih, sw, sh):

        iw = 100
        ih = 150
        sw = 75
        sh= 50

        A =matrix( [
            [1.0,0.0,-1.0,0.0,ih/iw] #ih/iw comes here for portrait
            ,[0.0,1.0,0.0,-1.0, -1] #iw/ih comes here for landscape
        ])
        b=matrix([float(sw),float(sh),0.0,0.0,0.0])
        c = matrix([-1.0,-1.0])
        sol=solvers.lp(c,A,b)
        print(sol['x'])
        x = int(sol['x'][0])
        y = int(sol['x'][1])
        print(x,y)
        # sol = LPSolver()
        # print(sol.solve(A,b,c))

        # A = matrix([ [-1.0, -1.0, 0.0, 1.0], [1.0, -1.0, -1.0, -2.0] ])
        # b = matrix([ 1.0, -2.0, 0.0, 4.0 ])
        # c = matrix([ 2.0, 1.0 ])
        # sol=solvers.lp(c,A,b)
        # print(sol['x'])
        return x

