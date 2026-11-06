"""Same restyled scene as scene2, with cameras pulled back into the far corners for depth."""
import math, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene4 as S

def yaw_to(cx, cz, tx, tz):
    return math.atan2(tx - cx, -(tz - cz))

def view(cx, cz, tx, tz, fov, drop, cy=1.25, sy=-0.06):
    return dict(cam=(cx, cy, cz, yaw_to(cx, cz, tx, tz), fov, 0.0, sy), drop=drop)

S.VIEWS = {
    # from the south-east corner, looking across to the shampoo / reception wall
    'north': view(6.45, 3.30, 2.3, 0.0, 80, {'chairs_cut', 'divider', 'doormat'}),
    # from beside the entrance, looking down the long axis to the house-side wall
    'east':  view(0.55, 1.05, 6.76, 2.45, 80, {'waiting', 'entrance', 'plant'}),
    # from the shelf side, looking back toward the waiting area
    'west':  view(6.30, 1.80, 0.0, 2.35, 78, {'shelf_e', 'toilet'}),
    # from beside the shampoo station, looking toward the cut stations and toilet
    'south': view(6.50, 1.30, 3.9, 3.5, 80, {'shampoo', 'towel', 'partition'}),
}

if __name__ == '__main__':
    v, W, Hh, spp, path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    S.export(v, W, Hh, spp, path)
