import tkinter as tk
from tkinter import ttk

from cvxopt import matrix, solvers
import numpy as np
import cv2
# import PIL
from PIL import Image, ImageTk
import math

from core.tk.StatusBar import StatusBar
from core.BaseTunerUI import BaseTunerUI


class Canvas():
    # def __init__(self,master, sb:StatusBar, status_key) -> None:
    def __init__(self,master, ui:BaseTunerUI) -> None:
        # assume there is just the one pic for now
        self.canvas:tk.Canvas = tk.Canvas(master=master
                ,background="black",relief=tk.FLAT
                ,border=2)
        self.canvas.grid(in_=master,column=0,row=0,sticky="nswe")
        self.canvas.bind('<Configure>',self.on_canvas_resized)
        self.resiz=""
        self.images = {}
        # self.sb = sb
        # self.status_key = status_key
        self.master = master
        self.ui = ui
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
            express proportion between two (e.g., w - 1.5h = 0)
            express proportion between two from the other side to
            get rid of the less than - careful with the signs (e.g., 2/3w - h = 0)
            max width
            max height
        '''


        def get_new(iw,ih,screen_in_landscape, b,c):


            Al =matrix( [
                [1.0,0.0,-1.0,0.0, - 1.0]
                ,[0.0,1.0,0.0,-1.0, iw/ih] #iw/ih comes here for portrait
            ])
            Ap =matrix( [
                [1.0,0.0,-1.0,0.0, - ih/iw] #ih/iw comes here for portrait
                ,[0.0,1.0,0.0,-1.0, 1.0]
            ])
            sol=solvers.lp(c,Al,b)
            # solver generally returns less than the max by one
            nwl = int(sol['x'][0]) + 1
            nhl = int(sol['x'][1]) + 1

            sol=solvers.lp(c,Ap,b)
            # solver generally returns less than the max by one
            nw = int(sol['x'][0]) + 1
            nh = int(sol['x'][1]) + 1

            if nwl != nw or nhl != nh:
                print(nwl - nw, nhl - nh)

            if screen_in_landscape:
            # screen is in landscape
            # get resize dimensions
                return nwl, nhl
            else:
                return nw, nh

        def get_screen_split(tsw,tsh):
            '''
            Returns True if you should use landscape, otherwise returns false
            '''
            w = h = 0
            for k in self.images:
                this = self.images[k]
                im = this["cvImage"]
                w += im.shape[1]
                h += im.shape[0]

            # landscape
            lsw = (tsw - (separator * (num_images - 1)))/num_images
            lsh = tsh
            l = np.sqrt((tsw - lsw)**2 + (tsh - lsh)**2)

            psw = tsw
            psh = (tsh - (separator * (num_images - 1)))/num_images
            p = np.sqrt((tsw - psw)**2 + (tsh - psh)**2)

            # when rmsd is lower, waste is minimized
            # return screen split mode and how much space each image gets to display itself
            if l < p:
                # screen landscape - split horizontal panes (l,r)
                return True, lsw,lsh
            else:
                # screen portrait - split vertical panes (t,b)
                return False, psw,psh


        separator = 5
        num_images = len(self.images)
        if num_images == 0: return
        tsh = self.master.winfo_height()
        tsw = self.master.winfo_width()
        if tsh <= 0 or tsw <= 0: return

        landscape, sw,sh = get_screen_split(tsw,tsh)
        if sh <= 0 or sw <= 0: return

        # maximizing height and width
        # - mul by -1 since the optimizer is a cost minimizer
        c = matrix([1.0,1.0]) * -1
        for i,k in enumerate(self.images):
            this = self.images[k]
            if landscape:
                top = 0
                left = (i * sw ) + (i * separator)
            else:
                left = 0
                top = (i * sh ) + (i * separator)

            image = np.copy(this["cvImage"])
            w = image.shape[1]
            h = image.shape[0]

            # note we've added the relationship
            # between width and height twice here
            # This is to ensure "== 0" instead of
            # "<= 0 or >= 0". It works.

            A =matrix( [
                 [1.0,0.0,-1.0, 0.0, -1.0,  h/w]
                ,[0.0,1.0, 0.0,-1.0,  w/h, -1.0]
            ])
            # b for this image
            b =matrix([float(sw),float(sh),0.0,0.0,0.0, 0.0])

            sol=solvers.lp(c,A,b)
            # solver generally returns less than the max by one
            nw = int(sol['x'][0]) + 1
            nh = int(sol['x'][1]) + 1
            if not math.isclose(nw/nh,w/h, rel_tol=10**-1):
                self.resize_mode = "BAD"
            else:
                self.resize_mode = "SAMPL" if nw <= w else "INTER"
            # if self.sb is not None: self.sb[self.status_key] = self.resize_mode
            self.ui.sampling = self.resize_mode

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
            x = ((sw - nw) // 2) + left
            y = ((sh - nh) // 2) + top
            self.canvas.create_image((x,y),image=this["photo_ref"],anchor="nw")

    # def simple_resize(self, iw, ih, sw, sh):
    #     w = False
    #     h = False
    #     fx = None
    #     fy = None
    #     if sw > sh:
    #         # screen wider than it is tall
    #         # w=True
    #         if iw > ih:
    #             # and the image is wider
    #             # reshape to a width aspect ration
    #             w=True
    #             fy = fx = sw/iw
    #         else:
    #             # image is taller
    #             # reshape to a height aspect ratio
    #             h = True
    #             fy = fx = min(sw/iw, sh/ih)
    #     else:
    #         # screen taller than it is wide
    #         # h = True
    #         if ih > iw:
    #             # and the image is taller than it is wide
    #             # reshape to a height aspect ratio
    #             h = True
    #             fx = fy = sh/ih
    #         else:
    #             # image is wider
    #             # reshape to a width aspect ration
    #             w=True
    #             fy = fx = min(sw/iw, sh/ih)


    #     # random, huh?
    #     fx *= 1.2
    #     fy *= 1.2

    #     return fx,fy

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

