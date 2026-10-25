# CNC-Mesa

Apply `$code-boundary-standards` before code changes and `$pcb-routing-standards` for board work.

- `firmware` composes the board profile and HostMot2 library into an ISE project.
- `linuxcnc` owns LinuxCNC configuration and runtime integration.
- `hostmot2/upstream` is an immutable Mesa source snapshot. Preserve its licenses and hashes. Board-specific changes belong in `firmware`.
- `mesa` owns the board description, original firmware and the public `mesa_firmware` Python API.
- `homing` exposes the standard LinuxCNC HOMEMOD API; its C implementation is a documented LinuxCNC source fork. Test it through HAL pins and the public API.
- Packages must not depend on apps. Apps may use documented package entry points.
- Run `make check`, `make test-hdl` and `make test-homing` before pushing. HDL analysis/simulation is not a substitute for ISE implementation/timing checks or board verification.
- Never describe reconstructed source as the vendor's recovered original project. Do not flash firmware as part of tests.
