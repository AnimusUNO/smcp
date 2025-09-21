# Licensing Update Summary

## Overview
This document summarizes the comprehensive licensing structure update for the Animus Letta MCP project, transitioning from a single CC-BY-SA 4.0 license to a dual-licensing approach.

## New Licensing Structure

### 1. Code License: GNU Affero General Public License v3.0 (AGPLv3)
- **File**: `LICENSE`
- **Scope**: All source code, including Python files, scripts, and executable code
- **Purpose**: Ensures that any derivative works remain open source and accessible to the community
- **Key Requirements**: 
  - Source code must be made available when software is run over a network
  - Derivative works must also be licensed under AGPLv3
  - Full source code must be provided with any distribution

### 2. Documentation & Data License: Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA 4.0)
- **File**: `LICENSE-DOCS`
- **Scope**: All documentation, data files, markdown files, and non-code content
- **Purpose**: Allows flexible sharing and adaptation of documentation while maintaining attribution
- **Key Requirements**:
  - Attribution to original author required
  - Derivative works must use the same license

## Files Updated

### Core License Files
1. **`LICENSE`** - Updated from CC-BY-SA 4.0 to full AGPLv3 text
2. **`LICENSE-DOCS`** - New file containing CC-BY-SA 4.0 for documentation

### Project Configuration Files
3. **`README.md`** - Updated badges, license section, and dual licensing explanation
4. **`CHANGELOG.md`** - Updated license change entry
5. **`smcp/__init__.py`** - Updated `__license__` variable from "CC-BY-SA 4.0" to "AGPLv3"

### Source Code Files (Added AGPLv3 Headers)
6. **`smcp/mcp_server.py`** - Main server file with full AGPLv3 header
7. **`smcp/plugins/botfather/cli.py`** - BotFather plugin with AGPLv3 header
8. **`smcp/plugins/devops/cli.py`** - DevOps plugin with AGPLv3 header
9. **`tests/conftest.py`** - Test configuration with AGPLv3 header
10. **`run_tests.py`** - Test runner script with AGPLv3 header

## Key Changes Made

### Badge Updates
- **Before**: Single CC-BY-SA 4.0 badge
- **After**: Dual badges showing AGPLv3 for code and CC-BY-SA 4.0 for documentation

### License Section Updates
- **Before**: Single license reference to CC-BY-SA 4.0
- **After**: Comprehensive dual licensing explanation with important AGPLv3 copyleft notice

### Source Code Headers
- Added standard AGPLv3 copyright headers to all major Python source files
- Headers include full license text and copyright notice
- Consistent formatting across all files

### Package Metadata
- Updated `__license__` variable in main package `__init__.py`
- Ensures package metadata reflects correct licensing

## Legal Implications

### AGPLv3 Requirements
- **Network Use**: If the software is used over a network (including web services), the complete source code must be made available to users
- **Derivative Works**: Any modifications or derivative works must also be licensed under AGPLv3
- **Source Distribution**: Full source code must be provided with any distribution

### CC-BY-SA 4.0 Requirements
- **Attribution**: Proper credit must be given to the original author
- **ShareAlike**: Derivative documentation must use the same license

## Compliance Notes

### For Contributors
- All code contributions automatically fall under AGPLv3
- Documentation contributions fall under CC-BY-SA 4.0
- Contributors retain copyright but grant license rights

### For Users
- **Code Use**: Must comply with AGPLv3 terms, especially for network services
- **Documentation Use**: Must comply with CC-BY-SA 4.0 terms
- **Commercial Use**: Both licenses permit commercial use with compliance

### For Distributors
- Must provide complete source code when distributing AGPLv3-licensed code
- Must maintain attribution for CC-BY-SA 4.0 licensed content
- Must include appropriate license notices

## Verification Checklist

- [x] Main LICENSE file updated to AGPLv3
- [x] LICENSE-DOCS file created for CC-BY-SA 4.0
- [x] README.md updated with dual licensing information
- [x] CHANGELOG.md updated to reflect changes
- [x] Package `__init__.py` updated with correct license
- [x] All major Python source files have AGPLv3 headers
- [x] Badges updated to show both licenses
- [x] License section explains dual licensing structure
- [x] Important AGPLv3 copyleft notice included

## Next Steps

1. **Review**: Ensure all changes meet project requirements
2. **Test**: Verify that licensing information is correctly displayed
3. **Document**: Update any additional documentation that may reference licensing
4. **Communicate**: Inform contributors and users about the new licensing structure
5. **Monitor**: Ensure ongoing compliance with both license types

## Contact

For questions about licensing or compliance:
- **Author**: Mark Rizzn Hopkins
- **Website**: https://animus.uno
- **License Files**: See `LICENSE` and `LICENSE-DOCS` in the project root

---

*This summary was generated as part of the comprehensive licensing structure update on January 2025.*
