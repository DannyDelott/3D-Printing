"""Shared physical interface between replaceable profile jigs and the tote grip.

Every interchangeable caul exposes the same straight mounting land:

- 31.75 mm overall width
- a centered flat top with 1.5 mm chamfers on both edges
- at least 7.4 mm of side depth through the mounting area

The tote saddle locates on width and top, while two M3 thumb screws provide
retention.  The profiled contact face remains owned by each individual jig.
"""

ATTACHMENT_WIDTH = 31.75
ATTACHMENT_TOP_CHAMFER = 1.5
ATTACHMENT_MINIMUM_SIDE_DEPTH = 7.4

# Diametral and vertical FDM fit allowances used by the tote saddle.
SADDLE_WIDTH_CLEARANCE = 0.50
SADDLE_TOP_CLEARANCE = 0.30
