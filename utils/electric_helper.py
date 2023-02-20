'''
Electric Field Helper Utilties

Kolby Kiesling
02/20/2023
'''
import numpy as np
from io import BytesIO, StringIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.patches import Circle
import base64
from werkzeug.datastructures import FileStorage
import pandas as pd

class Electric_Helper:
    '''
    Helper utility class for summing vectors and generating figures of electric fields
    '''
    def __init__(self, k=1, positive_color='#aa0000', negative_color='#0000aa', scale=0.15, x_border=5, y_border=5, cmap='hot') -> None:
        '''
        Mods to make:
            * k => Adjust the coloumb constant (DEFAULT 1)
            * postive_color => any hex color desired (DEFAULT RED)
            * negative_color => any hex color desired (DEFAULT BLUE)
            * scale => scale of charges on figure (DEFAULT 0.15)
            * x_border => adjust the size of the figure (DEFAULT 5)
            * y_border => adjust the size of the figure (DEFAULT 5)
            * cmap => Set the CMAP that will be used for the contour plot (DEFAULT 'hot')
        '''
        self.k = k
        self.r_list = []
        self.q_list = []
        self.x_list = []
        self.y_list = []
        self.potential = 0 # Global potential
        # If using contour fill
        self.levels = np.array([10** pw for pw in np.linspace(-2, 5, 20)])
        self.X = np.linspace(-1 * x_border, x_border, 1000)
        self.Y = np.linspace(-1 * y_border, y_border, 1000)
        self.X, self.Y = np.meshgrid(self.X, self.Y)
        self.charge_colors = {True: positive_color, False: negative_color}
        self.Ex = 0
        self.Ey = 0
        self.scale = scale
        self.x_boundary = x_border
        self.y_boundary = y_border
        self.cmap = cmap
    
    def generate_figure(self):
        '''
        Attempt to generate a figure for our electric field
        
        Will iterate over all charges held in this object and sum the potentials.

        Returns a byte object of the figure generated
        '''
        if len(self.q_list) != len(self.r_list):
            print('Something weird happend, the lengths of data are uneven, check your data please!')
            return
        
        self.potential = 0 # reinitialize to zero

        for i in range(len(self.q_list)):
            self.potential += (self.k * self.q_list[i]) / self.r_list[i] # sum the potentials

        self.Ex, self.Ey = np.gradient(-1 * self.potential, 0.01, 0.01) # Take the gradient to get the E field

        fig = Figure(figsize=(8, 8))
        ax = fig.add_subplot(1,1,1)

        contour_plot = ax.contourf(self.X, self.Y, self.potential, levels=self.levels, colors='k') # make the contour with the equipotentials
        ax.contourf(self.X, self.Y, self.potential, cmap=self.cmap) # levels seems to work weird here

        ax.clabel(contour_plot, inline=1, fontsize=8, rightside_up=True, colors= 'white' if self.cmap == 'hot' else 'k') # add labels

        ax.streamplot(self.X, self.Y, self.Ex, self.Ey, linewidth=0.5, color='white')

        for i in range(len(self.q_list)):
            ax.add_artist(
                Circle(
                (self.x_list[i], self.y_list[i]),           # set the x, y coordinates to drop the charge
                self.q_list[i] * self.scale,                # scale the charge so it is visible and not too big
                color=self.charge_colors[self.q_list[i]>0]) # set the color of the charge
            )

        ax.set_xlabel(r'$X$')
        ax.set_ylabel(r'$Y$')
        ax.set_title('{} Charge System'.format(len(self.q_list)))

        # Capture the figure as a PNG and return it to be rendered in HTML
        output = BytesIO() # Captured in memory
        FigureCanvas(fig).print_png(output)

        encoded_fig = base64.b64encode(output.getvalue())
        return encoded_fig.decode('utf-8')
    
    def sum_vectors(self, qi : float, xi : float, yi : float) -> None:
        '''
        Take the data we already have and sum against it,
        wahoo!
        '''
        self.x_list.append(xi)
        self.y_list.append(yi)
        self.q_list.append(qi)

        # Calculate the new r vector after adding all this data
        r_val = np.sqrt((self.X - xi) ** 2 + (self.Y - yi) ** 2)
        self.r_list.append(r_val)

    def parse_csv_file(self, csv_file : FileStorage):
        '''
        Parse CSV file to add to our vectors,
        skip over fields that are redundant in X, Y coords
        '''
        seen_coords = []
        df = pd.read_csv(csv_file, names=['charge', 'x', 'y'])
        print(df.head())
        for i, row in df.iterrows():
            if (row['x'], row['y']) not in seen_coords:
                self.sum_vectors(row['charge'], row['x'], row['y'])
                seen_coords.append((row['x'], row['y']))
            else:
                continue

    def reset_values(self) -> None:
        '''
        Reset tracked values to zero or initialized values
        '''
        self.r_list = []
        self.q_list = []
        self.x_list = []
        self.y_list = []
        self.potential = 0 # Global potential
        self.Ex = 0
        self.Ey = 0

    def write_csv_file(self, q_list : list, x_list : list, y_list : list):
        print(q_list)
        print(x_list)
        print(y_list)

        output = StringIO()
        for i in range(len(q_list)):
            output.write('{},{},{}\n'.format(
                    q_list[i], x_list[i], y_list[i]
                ))
 
        return output

    def generate_csv_line(self, charge_type='hline', xi=0, yi=0, qi=1, length='inf'):
        '''
        Return a CSV object of the charge(s) the user wants
        TYPES:
            * Point => Accepts:
                * xi -> initial position to center on
                * yi -> initial position to center on
                * charge_type: 'point'
            * hline => Accepts:
                * xi -> initial position to center on
                * yi -> initial position to center on
                * length: how long the line should be 
        '''
        output = None
        inf_bound = 2
        q_list, x_list, y_list = [], [], []
        STEP = 0.5
        if charge_type == 'hline':
            if length == 'inf':
                x_loc = -1 * inf_bound * self.x_boundary
                while x_loc <= inf_bound * self.x_boundary:
                    q_list.append(qi)
                    x_list.append(x_loc)
                    y_list.append(yi)

                    x_loc += STEP
            else:
                length = int(length)
                for x in range(int(-1 * length / 2), int(length / 2)):
                    q_list.append(qi)
                    x_list.append(x)
                    y_list.append(yi)
        
        elif charge_type == 'vline':
            if length == 'inf':
                y_loc = -1 * inf_bound * self.y_boundary
                while y_loc <= inf_bound * self.y_boundary:
                    q_list.append(qi)
                    x_list.append(xi)
                    y_list.append(y_loc)

                    y_loc += STEP
            else:
                length = int(length)
                for y in range(int(-1 * length / 2), int(length / 2)):
                    q_list.append(qi)
                    x_list.append(xi)
                    y_list.append(y)
        
        return self.write_csv_file(q_list, x_list, y_list)
    
    def generate_csv_circle(self, ri=1, xi=0, yi=0, qi=1):
        '''
        Return a CSV object of a circle with radius ri
        '''
        output = None
        q_list, x_list, y_list = [], [], []
        STEP = 10
        
        theta = 0
        while theta <= 360:
            x_new = ri * np.cos(theta * np.pi / 180 ) + xi
            y_new = ri * np.sin(theta * np.pi / 180 ) + yi
        
            q_list.append(qi)
            x_list.append(x_new)
            y_list.append(y_new)
            theta += STEP
        
        return self.write_csv_file(q_list, x_list, y_list)