# Camera, Seeding, Solar - Parallel Implementation Guide

**Created:** 2026-06-23  
**Status:** Ready to Start  
**Agents:** Bob & Codex

---

## 🎯 Quick Start

### For Codex (Backend Developer)
1. Read [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md) - Your tasks are in the "Codex Tasks" section
2. Start with **Phase 1: Camera Context Foundation** (Week 1-2)
3. Document all API decisions in [`camera-seeding-solar-collab-feedback.md`](camera-seeding-solar-collab-feedback.md)
4. Check feedback file daily for Bob's API requests

### For Bob (UI Developer)
1. Read [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md) - Your tasks are in the "Bob Tasks" section
2. Start with **Phase 1: Camera & Gimbal Control UI** (Week 1-2)
3. Review API contracts in [`camera-seeding-solar-collab-feedback.md`](camera-seeding-solar-collab-feedback.md)
4. Request API changes in feedback file if needed

---

## 📁 File Structure

```
docs/project/
├── README-COLLABORATION.md                              ← You are here
├── camera-seeding-solar-implementation-plan.md          ← Main plan with checkboxes
├── camera-seeding-solar-collab-feedback.md              ← Coordination file
├── camera-seeding-solar-collab-plan.md                  ← Original collaboration plan
└── comprehensive-camera-seeding-solar-implementation.md ← Full specification
```

---

## 🔄 Workflow

### Daily Routine

**Both Agents:**
1. Check [`camera-seeding-solar-collab-feedback.md`](camera-seeding-solar-collab-feedback.md) for new entries
2. Work on your assigned tasks from [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md)
3. Update feedback file with progress, blockers, or questions
4. Check off completed tasks in implementation plan

### When You Need to Edit a Shared File

**Shared files:**
- `tools/ui/context/mission_context.py`
- `tools/ui/service_locator.py`
- `tools/ui/context/__init__.py`

**Process:**
1. Write entry in feedback file: "Planning to edit [file] for [reason]"
2. Wait for other agent to acknowledge (or 24 hours)
3. Make your changes
4. Write entry in feedback file: "Completed changes to [file]"

### When You Have a Blocker

**Write in feedback file:**
```markdown
### YYYY-MM-DDTHH:MM:SSZ | [Your Name] | Blocker | [Files]

**Message:**
[Clear description of blocker]

**Needed from other agent:**
[Specific request]
```

### When You Complete a Phase

**Write in feedback file:**
```markdown
### YYYY-MM-DDTHH:MM:SSZ | [Your Name] | Progress | Phase Complete

**Message:**
Completed Phase [N]: [Phase Name]

**Deliverables:**
- [x] File 1
- [x] File 2
- [x] Tests

**Ready for:**
[What the other agent can now do]
```

---

## 📋 Work Division Summary

### Codex Owns (Backend)
- `tools/ui/context/camera_context.py` ✨ NEW
- `tools/ui/backend.py` (camera delegation)
- `skymeshx/models/observation_uav.py` (camera methods)
- `skymeshx/models/capabilities.py` ✨ NEW
- `skymeshx/control/solar_inspection.py` (preview data)
- `skymeshx/control/seeding_planner.py` (preview data)
- `tests/test_camera_context.py` ✨ NEW
- `tests/test_capability_registry.py` ✨ NEW
- All backend tests

### Bob Owns (Frontend)
- `tools/ui/qml/panels/GimbalPanel.qml` (camera controls)
- `tools/ui/qml/panels/SolarInspectionPanel.qml` ✨ NEW
- `tools/ui/qml/panels/SeedingPanel.qml` ✨ NEW
- `tools/ui/qml/MapView.qml` (overlays)
- `tools/ui/qml/main.qml` (integration)
- `tools/ui/qml/panels/MissionPanel.qml` (mode selection)

### Shared (Coordinate First)
- `tools/ui/context/mission_context.py` (upload/execute separation)
- `tools/ui/service_locator.py` (context registration)
- `tools/ui/context/__init__.py` (context exports)

---

## 🎯 Critical Success Factors

### 1. Upload ≠ Execute
**Rule:** Mission upload must NEVER automatically start the mission.

**Codex:** Ensure `mission_context.py` has separate upload and execute methods.  
**Bob:** Show clear "Upload Mission" and "Start Mission" buttons in wizards.

### 2. Hardware-Free Tests
**Rule:** All tests must work without MAVLink, ROS2, SITL, or real cameras.

**Codex:** Use fake connections and mock objects in all tests.  
**Bob:** Test UI with mock backend contexts.

### 3. Show Warnings, Don't Hide
**Rule:** Missing hardware shows warnings, doesn't hide modes.

**Codex:** Capability checks return warnings, not errors for optional hardware.  
**Bob:** Display warnings in wizard Step 1, allow user to proceed.

### 4. API First
**Rule:** Define interfaces before implementation.

**Codex:** Document API in feedback file before coding.  
**Bob:** Review API and request changes before building UI.

### 5. No Simultaneous Edits
**Rule:** Never edit the same file at the same time.

**Both:** Check file ownership in plan, coordinate in feedback file.

---

## 📅 Timeline (9 Weeks)

| Week | Codex | Bob |
|------|-------|-----|
| 1-2 | Camera context + tests | Camera UI controls |
| 3 | Capability registry + tests | Solar wizard (Steps 1-2) |
| 4 | Solar backend extensions | Solar wizard (Steps 3-4) |
| 5 | Seeding backend extensions | Seeding wizard (Steps 1-3) |
| 6 | Seeding validation + tests | Seeding wizard (Steps 4-6) |
| 7 | Mission context review | Map overlays |
| 8 | Integration testing | Main QML integration |
| 9 | Documentation + polish | UI testing + polish |

---

## 🔍 API Contracts

All API contracts are documented in [`camera-seeding-solar-collab-feedback.md`](camera-seeding-solar-collab-feedback.md).

**Current APIs:**
- ✅ Camera Context (properties, slots, signals)
- ✅ Capability Registry (check methods)
- ✅ Solar Preview Data (format)
- ✅ Seeding Preview Data (format)

**Bob:** If you need additional properties, slots, or different data formats, request them in the feedback file.

**Codex:** Review Bob's requests and implement or propose alternatives.

---

## 🧪 Testing Strategy

### Codex Tests
- Unit tests for all backend classes
- Use `FakeConnection`, `FakeMav` from `tests/conftest.py`
- Mock camera/gimbal responses
- Test error handling and fallback behavior
- Ensure 100% hardware-free operation

### Bob Tests
- UI component tests with mock contexts
- Wizard flow tests (step navigation)
- Map overlay rendering tests
- Error message display tests
- Mode switching tests

---

## 📊 Progress Tracking

**Check implementation plan:** [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md)

**Update checkboxes as you complete tasks:**
```markdown
- [x] Completed task
- [ ] Pending task
```

**Write progress updates in feedback file:**
```markdown
### YYYY-MM-DDTHH:MM:SSZ | [Your Name] | Progress | [Files]

**Message:**
Completed [task description]

**Next:**
Starting [next task]
```

---

## 🚨 Emergency Contacts

**If you're blocked and need immediate help:**
1. Write "BLOCKER" entry in feedback file
2. Tag with specific request for other agent
3. Continue with other tasks while waiting

**If you find a critical issue:**
1. Write "CRITICAL" entry in feedback file
2. Describe impact and proposed solution
3. Wait for acknowledgment before proceeding

---

## ✅ Definition of Done

### Phase Complete When:
- [ ] All checkboxes for that phase are checked
- [ ] All tests pass
- [ ] Code reviewed (self-review)
- [ ] Documentation updated
- [ ] Feedback file updated with completion entry

### Project Complete When:
- [ ] All 9 weeks of tasks completed
- [ ] Integration tests pass
- [ ] User documentation complete
- [ ] Both agents sign off in feedback file

---

## 📚 Reference Documents

1. **Implementation Plan** - [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md)
   - Detailed task list with checkboxes
   - Week-by-week breakdown
   - File ownership

2. **Feedback File** - [`camera-seeding-solar-collab-feedback.md`](camera-seeding-solar-collab-feedback.md)
   - API contracts
   - Progress updates
   - Blockers and questions

3. **Comprehensive Spec** - [`comprehensive-camera-seeding-solar-implementation.md`](comprehensive-camera-seeding-solar-implementation.md)
   - Full technical specification
   - User workflows
   - Safety requirements

4. **Original Collab Plan** - [`camera-seeding-solar-collab-plan.md`](camera-seeding-solar-collab-plan.md)
   - Initial work split proposal
   - Ground rules

5. **Agent Rules** - [`../../AGENTS.md`](../../AGENTS.md)
   - Repository-wide patterns
   - Testing conventions
   - Code style

---

## 🎉 Let's Build!

**Codex:** Start with creating `tools/ui/context/camera_context.py`  
**Bob:** Start with reviewing API contracts and planning UI layout

**Remember:**
- Check feedback file daily
- Document everything
- Test everything
- Coordinate on shared files
- Have fun! 🚀