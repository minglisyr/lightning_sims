import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button

plt.style.use('dark_background')

# Canvas limits
xlim = (-80, 80)
ylim = (0, 110)

# Color gradient from green to red
cmap = LinearSegmentedColormap.from_list("green_red", ["green", "red"])

# Parameters
branch_length = 7
max_steps = 120
connect_threshold = 12

def clamp(val, minval, maxval):
    return max(minval, min(val, maxval))

def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def random_branch(p, target, angle_spread=np.pi/2):
    # Bias direction toward target
    dx, dy = target[0] - p[0], target[1] - p[1]
    base_angle = np.arctan2(dy, dx)
    angle = base_angle + np.random.uniform(-angle_spread/2, angle_spread/2)
    length = branch_length * np.random.uniform(0.7, 1.3)
    new_x = clamp(p[0] + length * np.cos(angle), xlim[0], xlim[1])
    new_y = clamp(p[1] + length * np.sin(angle), ylim[0], ylim[1])
    return (new_x, new_y)

def find_connection(front1, front2, threshold=connect_threshold):
    for i, p1 in enumerate(front1):
        for j, p2 in enumerate(front2):
            if distance(p1, p2) < threshold:
                return i, j
    return None, None

def build_full_path(branches1, branches2, idx1, idx2):
    # Connect the two meeting branches
    path1 = branches1[idx1]
    path2 = branches2[idx2]
    return path1 + path2[::-1][1:]

fig, ax = plt.subplots(figsize=(6, 8))
plt.subplots_adjust(bottom=0.15)
ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.axis('off')

button_ax = plt.axes([0.4, 0.03, 0.2, 0.07])
regen_button = Button(button_ax, 'Regenerate', color='gray', hovercolor='lightgray')

# Store all plot artists for cleanup
lines1 = []
lines2 = []
main_line_segments = []
start_marker = None
end_marker = None
ani = None

def regenerate(event=None):
    global lines1, lines2, main_line_segments, start_marker, end_marker, ani

    # --- CLEANUP: Remove all previous artists ---
    for l in lines1:
        l.remove()
    lines1.clear()
    for l in lines2:
        l.remove()
    lines2.clear()
    for l in main_line_segments:
        l.remove()
    main_line_segments.clear()
    if start_marker is not None:
        start_marker.remove()
        start_marker = None
    if end_marker is not None:
        end_marker.remove()
        end_marker = None

    # --- Generate new random start and end points ---
    start = (np.random.uniform(xlim[0], xlim[1]), ylim[1])
    end = (np.random.uniform(xlim[0], xlim[1]), ylim[0])

    # --- Plot start and end markers ---
    start_marker, = ax.plot([start[0]], [start[1]], 'go', markersize=10)
    end_marker, = ax.plot([end[0]], [end[1]], 'ro', markersize=10)

    # --- Initialize fronts and branches ---
    front1 = [start]
    front2 = [end]
    branches1 = [[start]]
    branches2 = [[end]]
    segments1 = []
    segments2 = []
    met = False
    meet_idx1 = meet_idx2 = None

    # For animation: record the order of segment creation
    anim_segments = []

    # --- Simultaneous growth loop ---
    for step in range(max_steps):
        # Grow from start
        new_front1 = []
        new_branches1 = []
        for i, tip in enumerate(front1):
            new_tip = random_branch(tip, front2[0])
            segments1.append((tip, new_tip))
            anim_segments.append(('start', (tip, new_tip)))
            new_front1.append(new_tip)
            new_branches1.append(branches1[i] + [new_tip])
        front1 = new_front1
        branches1 = new_branches1

        # Grow from end
        new_front2 = []
        new_branches2 = []
        for i, tip in enumerate(front2):
            new_tip = random_branch(tip, front1[0])
            segments2.append((tip, new_tip))
            anim_segments.append(('end', (tip, new_tip)))
            new_front2.append(new_tip)
            new_branches2.append(branches2[i] + [new_tip])
        front2 = new_front2
        branches2 = new_branches2

        # Check for connection
        idx1, idx2 = find_connection(front1, front2)
        if idx1 is not None:
            met = True
            meet_idx1, meet_idx2 = idx1, idx2
            break

    # --- Build full path for color blending ---
    if met:
        full_path = build_full_path(branches1, branches2, meet_idx1, meet_idx2)
    else:
        # fallback: connect the last points
        full_path = branches1[0] + branches2[0][::-1][1:]

    # --- Prepare lines for animation ---
    for _ in range(len(segments1)):
        line, = ax.plot([], [], color=cmap(0.0), linewidth=2)
        lines1.append(line)
    for _ in range(len(segments2)):
        line, = ax.plot([], [], color=cmap(1.0), linewidth=2)
        lines2.append(line)

    total_frames = len(anim_segments) + len(full_path)

    def init():
        for line in lines1 + lines2:
            line.set_data([], [])
        for l in main_line_segments:
            l.set_data([], [])
        return lines1 + lines2 + main_line_segments

    def update(frame):
        # Animate the growth of both fronts
        if frame < len(anim_segments):
            seg_type, (xys, xye) = anim_segments[frame]
            if seg_type == 'start':
                idx = sum(1 for t, _ in anim_segments[:frame+1] if t == 'start') - 1
                lines1[idx].set_data([xys[0], xye[0]], [xys[1], xye[1]])
            else:
                idx = sum(1 for t, _ in anim_segments[:frame+1] if t == 'end') - 1
                lines2[idx].set_data([xys[0], xye[0]], [xys[1], xye[1]])
        else:
            # After meeting, animate the main path with gradient
            idx = frame - len(anim_segments)
            if idx > 0:
                xs = [p[0] for p in full_path[:idx+1]]
                ys = [p[1] for p in full_path[:idx+1]]
                # Remove previous main_line_segments
                for l in main_line_segments:
                    l.remove()
                main_line_segments.clear()
                # Color blending along the path
                for i in range(len(xs)-1):
                    color = cmap(i / max(1, len(xs)-2))
                    l, = ax.plot(xs[i:i+2], ys[i:i+2], color=color, linewidth=4, alpha=0.9)
                    main_line_segments.append(l)
        return lines1 + lines2 + main_line_segments

    if ani is not None and ani.event_source is not None:
        ani.event_source.stop()
    ani = FuncAnimation(fig, update, frames=total_frames, init_func=init,
                        interval=30, blit=True, repeat=False)
    fig.canvas.draw_idle()

regen_button.on_clicked(regenerate)
regenerate()
plt.show()
