import numpy as np
import matplotlib.pyplot as plt
import os

def random_black_white_rgba(n):
    step = 255 // (n-1)
    return [(i*step/255, i*step/255, i*step/255) for i in range(n)]    

def generate_randomcolor(n, toListedColormap=False, random_seed=22, grey=False):
    np.random.seed(random_seed)
    if grey:
        colors = random_black_white_rgba(n)
    else:
        colors = np.random.rand(n, 3) #生成50個RGB顏色
    if toListedColormap:
        import matplotlib.colors as mcolors
        colors = mcolors.ListedColormap(colors)
    return colors

def generate_colordict(itemList, color='random', trans_level=0.5, random_seed=22, grey=False):
    '''
    color要確認顏色是否夠用，不能比 itemList 長度還短
    '''
    
    if color == 'random':
        colors = generate_randomcolor(len(itemList), random_seed, grey)
    else:
        colors = plt.get_cmap(color).colors#(np.linspace(0, 1, len(itemList)))
    colors = transparent_cmap(colors, trans_level)
    color_dict = dict(zip(itemList, colors))
    return color_dict

def transparent_cmap(cmap, trans_level=0.5, tocmap=False):
    import matplotlib.colors as mcolors
    if type(cmap) != mcolors.ListedColormap:
        cmap = mcolors.ListedColormap(cmap)
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,-1] = trans_level
    if tocmap:
        my_cmap = mcolors.ListedColormap(my_cmap)
    return my_cmap


def save_fig(fig, fig_path, fig_name, dpi=300):
    if not os.path.exists(fig_path):
        os.makedirs(fig_path)
    fig.savefig(f'{fig_path}/{fig_name}.png', dpi=dpi)