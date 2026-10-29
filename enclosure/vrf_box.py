#!/usr/bin/env python3
"""Enclosure for the ESP32-C3 SuperMini + TJA1051T/3 CAN Pal. Writes vrf-box-base.stl and vrf-box-lid.stl.
usage: vrf_box.py   (needs manifold3d + numpy; Python 3.12 has wheels)

Layout (X = length, Y = width, Z = up): C3 at the -X end with USB-C through the wall, 5 mm gap for the
4 wires (and to keep the C3's chip antenna off the CAN Pal), CAN Pal at the +X end in a cradle (side rails + lips, no screws) with its
screw terminal facing a slot in the +X wall. Flat bottom for double-sided tape; friction-fit lid.
"""
import os, numpy as np
from manifold3d import Manifold

# --- measured ---
C3_L, C3_W, C3_PCB = 22.5, 18.0, 1.0        # SuperMini PCB (USB-C flush with the -X edge)
CP_L, CP_W, CP_PCB = 20.0, 20.0, 1.6        # CAN Pal PCB
CP_TALL = 11.0                               # tallest part above the CAN Pal PCB (screw terminal)
# --- guessed from photos: check with calipers before printing ---
USB_Z = 1.6                                  # USB-C centre above the C3 PCB top
CP_STANDOFF = 1.5                            # gap under the CAN Pal for solder joints (wires soldered to pads, no headers)
# --- design ---
WALL, FLOOR, CLR = 2.0, 1.6, 0.4
GAP = 5.0                                    # wires as soldered reach 6 mm; 1 mm of slack for the joints
C3_RAISE = 2.0                               # platform so the USB plug opening clears the floor
USB_OPEN_W, USB_OPEN_H = 12.5, 7.0           # fits a cable's plug overmold, not just the connector
SLOT_W = 14.0                                # bus wires into the screw terminal
LID_T, LIP_H, LIP_T, LIP_CLR = 2.0, 3.5, 1.2, 0.1   # print 2: 2.0 mm lip with 0.2 clearance was loose
SNAP_L, SNAP_H, SNAP_IN = 10.0, 1.6, 0.6     # snap bump on each long side of the lid lip: length, height, interference
SNAP_Z = 1.2                                 # bump centre above the lip's free end (leaves a ledge above the groove)
GROOVE_D, GROOVE_H = 0.9, 2.0                # matching groove in the base's long inner walls
HOLD_IN = 0.2                                # hold-down posts on the lid press this far into the boards
TERM_EXTRA = 2.0                             # print 2: terminal pad fell 2 mm short (terminal lower than CP_TALL)

IN_X = CLR + C3_L + GAP + CP_L + 1.0 + CLR   # +1: terminal overhang
IN_Y = max(C3_W, CP_W) + 2 * CLR
IN_Z = CP_STANDOFF + CP_PCB + CP_TALL + 1.0
OUT_X, OUT_Y, OUT_Z = IN_X + 2 * WALL, IN_Y + 2 * WALL, IN_Z + FLOOR


def box(x, y, z, at=(0, 0, 0)):
    return Manifold.cube([x, y, z]).translate(list(at))


def base():
    shell = box(OUT_X, OUT_Y, OUT_Z) - box(IN_X, IN_Y, IN_Z + 1, (WALL, WALL, FLOOR))
    y0 = WALL + (IN_Y - C3_W) / 2
    # C3: platform, end stop at the antenna end and side lips only over the last 6 mm; the wired pads
    # (G, 3.3, 4, 3) are near the USB end and their solder bulges past the castellated edge
    lip, pk, keep = 1.2, 0.3, 6.0
    c3 = box(C3_L + pk + lip, C3_W + 2 * (pk + lip), C3_RAISE + 1.5, (WALL, y0 - pk - lip, FLOOR)) \
        - box(C3_L + pk, C3_W + 2 * pk, 10, (WALL, y0 - pk, FLOOR + C3_RAISE)) \
        - box(C3_L - keep, C3_W + 2 * (pk + lip) + 2, 10, (WALL, y0 - pk - lip - 1, FLOOR + C3_RAISE))
    # CAN Pal: cradle, so the mounting holes don't matter. Rails under the two side edges, lips beside
    # them, corner stops at the wired (-X) edge whose pads bulge with solder; the +X wall stops it at the terminal end
    cp_x0 = WALL + IN_X - CLR - 1.0 - CP_L
    cy0 = WALL + (IN_Y - CP_W) / 2
    rail, lip, pk, corner = 2.0, 1.2, 0.3, 2.0
    lip_h = CP_STANDOFF + CP_PCB + 1.5
    cradle = Manifold()
    for y in (cy0 - pk - lip, cy0 + CP_W + pk):           # lips, outside the board's side edges
        cradle += box(CP_L + 1.0 + pk + lip, lip, lip_h, (cp_x0 - pk - lip, y, FLOOR))
    # end stops at the wired edge's two corners only (print 3 slid toward the C3); the middle stays open
    # for the soldered pads, so this assumes they sit more than `corner` mm in from each corner
    for y in (cy0 - pk - lip, cy0 + CP_W - corner):
        cradle += box(lip, corner + pk + lip, lip_h, (cp_x0 - pk - lip, y, FLOOR))
    for y in (cy0, cy0 + CP_W - rail):                     # rails, under the board's side edges
        cradle += box(CP_L + 1.0, rail, CP_STANDOFF, (cp_x0, y, FLOOR))
    # USB-C opening in the -X wall, centred on the connector
    usb_cz = FLOOR + C3_RAISE + C3_PCB + USB_Z
    usb = box(WALL + 2, USB_OPEN_W, USB_OPEN_H,
              (-1, WALL + IN_Y / 2 - USB_OPEN_W / 2, usb_cz - USB_OPEN_H / 2))
    # bus-wire slot in the +X wall, open to the top, starting just above the CAN Pal PCB
    slot_z = FLOOR + CP_STANDOFF + CP_PCB + 1.0
    slot = box(WALL + 2, SLOT_W, OUT_Z, (OUT_X - WALL - 1, WALL + IN_Y / 2 - SLOT_W / 2, slot_z))
    # snap grooves in the long inner walls, centred in X, level with the lid lip's bumps
    gz = OUT_Z - LIP_H + SNAP_Z - GROOVE_H / 2
    gx = OUT_X / 2 - (SNAP_L + 1.0) / 2
    grooves = box(SNAP_L + 1.0, GROOVE_D, GROOVE_H, (gx, WALL - GROOVE_D, gz)) \
        + box(SNAP_L + 1.0, GROOVE_D, GROOVE_H, (gx, WALL + IN_Y, gz))
    return shell + c3 + cradle - usb - slot - grooves


def lid():
    plate = box(OUT_X, OUT_Y, LID_T)
    lx, ly = IN_X - 2 * LIP_CLR, IN_Y - 2 * LIP_CLR
    lip = box(lx, ly, LIP_H, (WALL + LIP_CLR, WALL + LIP_CLR, LID_T)) \
        - box(lx - 2 * LIP_T, ly - 2 * LIP_T, LIP_H + 1, (WALL + LIP_CLR + LIP_T, WALL + LIP_CLR + LIP_T, LID_T - 0.5))
    # clear the bus-wire slot so the lip doesn't block it
    notch = box(LIP_T + 1, SLOT_W, LIP_H + 1, (WALL + IN_X - LIP_CLR - LIP_T - 0.5, WALL + IN_Y / 2 - SLOT_W / 2, LID_T))
    # snap bumps: triangular ridges on the outer faces of the long lip sides (45 deg flanks, no supports)
    zc, x0, x1 = LID_T + LIP_H - SNAP_Z, OUT_X / 2 - SNAP_L / 2, OUT_X / 2 + SNAP_L / 2
    bumps = Manifold()
    for face, out in ((WALL + LIP_CLR, -1), (WALL + LIP_CLR + ly, 1)):
        tip = face + out * (LIP_CLR + SNAP_IN)
        root = face - out * 0.2                            # start inside the lip so the union is solid
        bumps += Manifold.hull_points([[x, y, z] for x in (x0, x1) for y, z in
                                       ((root, zc - SNAP_H / 2), (root, zc + SNAP_H / 2), (tip, zc))])
    # hold-downs: the lid is flipped about X onto the base (notch over the bus-wire slot), so X is kept and
    # Y mirrors; every post is centred or paired in Y. Base-frame height h -> post length OUT_Z - h.
    def post(x0, x1, y0, y1, h, press):
        return box(x1 - x0, y1 - y0, OUT_Z - h + press, (x0, y0, LID_T))
    c3_top = FLOOR + C3_RAISE + C3_PCB
    y0 = WALL + (IN_Y - C3_W) / 2
    c3_end = WALL + C3_L
    holds = post(c3_end - 3.0, c3_end - 0.5, y0 + 0.3, y0 + 1.8, c3_top, HOLD_IN) \
        + post(c3_end - 3.0, c3_end - 0.5, y0 + C3_W - 1.8, y0 + C3_W - 0.3, c3_top, HOLD_IN)   # C3 antenna-end edges
    # USB-C shell top (USB_Z is a guess, so touch it without pressing)
    holds += post(WALL + LIP_CLR + LIP_T + 0.2, WALL + 6.0, WALL + IN_Y / 2 - 3.0, WALL + IN_Y / 2 + 3.0,
                  c3_top + 2 * USB_Z, 0.0)
    # CAN Pal: pad on the screw terminal's top, inside the lip notch
    t_top = FLOOR + CP_STANDOFF + CP_PCB + CP_TALL
    t_x1 = WALL + IN_X - 1.0
    holds += post(t_x1 - 5.0, t_x1, WALL + IN_Y / 2 - 4.0, WALL + IN_Y / 2 + 4.0, t_top, HOLD_IN + TERM_EXTRA)
    return plate + lip - notch + bumps + holds


def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(b"vrf_box".ljust(80, b"\0"))
        f.write(np.uint32(len(t)).tobytes())
        f.write(rec.tobytes())


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for name, part in (("vrf-box-base.stl", base()), ("vrf-box-lid.stl", lid())):
        write_stl(part, os.path.join(here, name))
        print(f"{name}: volume {part.volume():.0f} mm3, genus {part.genus()}")
    print(f"outside {OUT_X:.1f} x {OUT_Y:.1f} x {OUT_Z + LID_T:.1f} mm (with lid)")
