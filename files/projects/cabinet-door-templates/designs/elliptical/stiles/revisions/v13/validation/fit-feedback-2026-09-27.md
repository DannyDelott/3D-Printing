# V13 physical fit failure — 2026-09-27

The user reports that the full print is too tight and the socket arms bow during assembly. The supplied photo shows distortion along the outer template edge near the joint. The earlier V12 .05 coupon passed; that approval does not establish full-part fit. Do not recommend another full V13 print pending diagnosis.

Read-only audit on 2026-09-27:

- Reimported the V13 full-part STEP solids and the V12 .05 coupon STEP solids. Clipped both to the mating region (split − 10 mm through split + 18 mm, excluding the engraved label). Symmetric difference: 0.0 mm³ for both tongue and socket.
- Full V13 assembled CAD intersection: 0.0 mm³.
- Compared every project setting in the saved V11 comparison, V12 socket, and V13 full sliced 3MF archives: no differences.
- Saved V13 object and build transforms preserve the print orientation; no flip or scale was introduced.

These checks do not reproduce the printed bowing or identify its cause. Confirmation of the actual printed file, material/settings and assembly orientation is pending. Cross-fitting the existing successful coupon against each full-size half can isolate which printed mating surface differs without another print. No geometry or print file was changed in response to this report.
