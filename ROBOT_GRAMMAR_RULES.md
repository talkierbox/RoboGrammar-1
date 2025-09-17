# RoboGrammar Rule Index Mapping

## Overview

Robot designs in RoboGrammar are generated using **rule sequences** - arrays of integers that correspond to grammar transformation rules. Each integer maps to a specific rule that modifies the robot's structure.

**Grammar File**: `data/designs/grammar_apr30.dot`  
**Total Rules**: 20 (indices 0-19)

## Rule Index Mapping

### **Structural Rules (Basic Robot Assembly)**

**Rule 0: `make_robot`**
- **Function**: Creates the initial robot structure
- **Transforms**: `robot` → `head-body-tail` chain
- **Usage**: Must be the first rule in any sequence
- **Components Added**: head, body, tail connected by body_joints

**Rule 1: `append_body`**
- **Function**: Adds a body segment before the tail
- **Transforms**: `parent → tail` → `parent → body → tail`
- **Usage**: Extends robot body length
- **Components Added**: Additional body segment

**Rule 2: `make_body_with_legs`**
- **Function**: Converts body into a limbed segment with bilateral legs
- **Transforms**: `body` → `body + 2×(limb_mount → limb_link → limb)`
- **Properties**: Creates capsule body (length=0.15, radius=0.045)
- **Components Added**: 2 limb_mounts, 2 limb_links, 2 limbs (left/right)

**Rule 3: `make_body_without_legs`**
- **Function**: Converts body into a simple capsule segment
- **Transforms**: `body` → capsule body (no limbs)
- **Properties**: Creates capsule body (length=0.15, radius=0.045)
- **Components Added**: None (just finalizes body shape)

### **Limb Extension Rules**

**Rule 4: `append_limb_link`**
- **Function**: Adds a limb segment to extend leg length
- **Transforms**: `parent → limb` → `parent → limb_link → limb`
- **Usage**: Makes legs longer by adding joints
- **Components Added**: Additional limb_link with limb_joint

**Rule 5: `end_limb`**
- **Function**: Terminates limb construction (removes limb placeholder)
- **Transforms**: `parent → limb` → `parent`
- **Usage**: Finalizes leg construction
- **Components Added**: None (cleanup rule)

### **Termination Rules**

**Rule 6: `end_tail`**
- **Function**: Removes tail placeholder
- **Transforms**: `parent → tail` → `parent`
- **Usage**: Finalizes rear of robot
- **Components Added**: None (cleanup rule)

**Rule 7: `end_head`**
- **Function**: Removes head placeholder  
- **Transforms**: `head → child` → `child`
- **Usage**: Finalizes front of robot
- **Components Added**: None (cleanup rule)

### **Limb Link Shapes**

**Rule 8: `make_normal_limb_link`**
- **Function**: Creates standard limb segment
- **Properties**: Capsule shape (length=0.1, radius=0.025)
- **Usage**: Default leg segment size
- **Components Added**: Standard-sized limb link

**Rule 9: `make_long_limb_link`**
- **Function**: Creates extended limb segment
- **Properties**: Capsule shape (length=0.15, radius=0.025)
- **Usage**: Longer leg segments for increased reach
- **Components Added**: Long limb link

### **Body Joint Types**

**Rule 10: `make_fixed_body_joint`**
- **Function**: Creates rigid body connection
- **Joint Type**: Fixed (no movement)
- **Usage**: Creates stiff spinal connections
- **Motion**: None

**Rule 11: `make_roll_body_joint`**
- **Function**: Creates rolling body joint
- **Joint Type**: Hinge around X-axis (roll)
- **Usage**: Allows body segments to roll left/right
- **Motion**: Rotation around forward axis

**Rule 12: `make_swing_body_joint`**
- **Function**: Creates swinging body joint
- **Joint Type**: Hinge around Y-axis (pitch)  
- **Color**: Green (0, 0.5, 0)
- **Usage**: Allows body to bend up/down
- **Motion**: Vertical flexion

**Rule 13: `make_lift_body_joint`**
- **Function**: Creates lifting body joint
- **Joint Type**: Hinge around Z-axis (yaw)
- **Usage**: Allows body to turn left/right
- **Motion**: Horizontal rotation

### **Limb Joint Types**

**Rule 14: `make_left_roll_limb_joint`**
- **Function**: Creates left-side rolling limb joint
- **Joint Type**: Hinge around X-axis
- **Orientation**: -90° around Y-axis
- **Usage**: Left leg roll motion
- **Motion**: Inward/outward leg rotation

**Rule 15: `make_right_roll_limb_joint`**
- **Function**: Creates right-side rolling limb joint
- **Joint Type**: Hinge around X-axis
- **Orientation**: +90° around Y-axis  
- **Usage**: Right leg roll motion
- **Motion**: Inward/outward leg rotation

**Rule 16: `make_swing_limb_joint`**
- **Function**: Creates swinging limb joint
- **Joint Type**: Hinge around Y-axis
- **Color**: Green (0, 0.5, 0)
- **Usage**: Forward/backward leg swing
- **Motion**: Leg flexion/extension

**Rule 17: `make_acute_lift_limb_joint`**
- **Function**: Creates upward-angled limb joint
- **Joint Type**: Hinge around Z-axis
- **Angle**: 120° (acute angle)
- **Usage**: Limbs angled upward
- **Motion**: Upward-oriented leg movement

**Rule 18: `make_obtuse_lift_limb_joint`**
- **Function**: Creates moderately-angled limb joint  
- **Joint Type**: Hinge around Z-axis
- **Angle**: 60° (obtuse angle)
- **Usage**: Limbs angled moderately
- **Motion**: Moderate-angle leg movement

**Rule 19: `make_backwards_lift_limb_joint`**
- **Function**: Creates backward-angled limb joint
- **Joint Type**: Hinge around Z-axis
- **Angle**: -60° (backward angle)
- **Usage**: Limbs angled backward
- **Motion**: Backward-oriented leg movement

## Usage Examples

### Simple Quadruped
```
[0, 7, 2, 8, 16, 8, 16, 5, 5, 6]
```
- `0`: Create basic robot (head-body-tail)  
- `7`: Remove head
- `2`: Add legs to body
- `8`: Make normal limb links
- `16`: Add swing joints to legs
- `8`: Add more limb links  
- `16`: Add more swing joints
- `5,5`: End both limbs
- `6`: Remove tail

### Walking Robot (from README)
```
[0, 12, 7, 1, 12, 3, 10, 1, 3, 1, 12, 12, 1, 3, 10, 2, 16, 8, 1, 3, 12, 4, 1, 3, 2, 12, 18, 9, 18, 8, 5, 5, 1, 12, 6, 3]
```
- Creates multi-segment body with various joint types
- Adds legs with different orientations and lengths
- Uses swing, roll, and lift joints for complex locomotion

## Rule Application Process

1. **Start**: Single 'robot' node
2. **Rule 0**: Must be first - creates head-body-tail structure  
3. **Body Construction**: Rules 1,2,3 build body segments
4. **Limb Construction**: Rules 4,5,8,9 build legs
5. **Joint Configuration**: Rules 10-19 set movement types
6. **Termination**: Rules 5,6,7 clean up placeholders

## Design Constraints

- **Rule 0** must be first in any valid sequence
- **Termination rules** (5,6,7) remove placeholders and must be used appropriately
- **Joint rules** (10-19) only work on existing joint placeholders
- **Shape rules** (8,9) only work on limb_link placeholders
- Rules are applied sequentially - later rules operate on the result of earlier ones

## Physical Properties

- **Body segments**: Capsule shape, radius=0.045, density=3.0
- **Limb segments**: Capsule shape, radius=0.025
- **Normal limbs**: length=0.1  
- **Long limbs**: length=0.15
- **Limb mounts**: length=0.1, radius=0.025

This rule system enables systematic generation of diverse robot morphologies through combinatorial rule application.