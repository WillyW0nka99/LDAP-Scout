
# LDAP Parsing Tool

This tool parses LDAP output from a file, identifies and displays non-standard fields, and offers various filtering options. It’s designed for users who need to analyze LDAP data, quickly identify unique attributes, and filter out irrelevant information.

## Features

- **Non-Standard Field Detection**: Highlights fields not typically found in LDAP entries.
- **Field Filtering**: Exclude or include specific fields from the output.
- **Threshold Levels**: Control the threshold for rare standard fields to be displayed.
- **Field and User Listing**: List all fields with occurrence counts and list all users with highlighting for those with unique fields.
- **Customizable Output**: Easily include or exclude specific fields from the results.

## Requirements

- Python 3.6+
- `colorama` library for colorized terminal output.

### Installation

1. Clone this repository or download `ldap-u.py`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with an LDAP output file and choose your options:

```bash
python3 ldap-u.py <input_file> [OPTIONS]
```

### Example LDAP Search

To get LDAP output compatible with this tool:
```bash
ldapsearch -x -LLL -H ldap://<LDAP_SERVER> -D '<bind_dn>' -w <password> -b '<base_dn>' '(objectClass=user)' '*'
```

### Options

| Flag               | Description                                                                                               |
|--------------------|-----------------------------------------------------------------------------------------------------------|
| `--exclude`        | Exclude specified fields from output. Example: `--exclude field1 field2`                                  |
| `--include`        | Include specified fields in output, adding them to users with non-standard data.                          |
| `--include-all`    | Show all users containing specified fields, in addition to regular results.                               |
| `--list-fields`    | List all fields found in LDAP data with their occurrence counts. Non-standard fields shown in red.        |
| `--list-users`     | List all users, highlighting users with non-standard fields in red and rare fields in yellow.             |
| `--level`          | Set threshold level for rare standard fields (1 = 10%, 5 = 95%). Default level is 2 (25%).               |

### Examples

1. **List All Fields in LDAP Data**:
   ```bash
   python3 ldap-u.py ldap_output.txt --list-fields
   ```

2. **List All Users**:
   ```bash
   python3 ldap-u.py ldap_output.txt --list-users
   ```

3. **Exclude Specific Fields**:
   ```bash
   python3 ldap-u.py ldap_output.txt --exclude memberOf description
   ```

4. **Include a Specific Field in Output**:
   ```bash
   python3 ldap-u.py ldap_output.txt --include info
   ```

5. **Use Threshold to Control Rare Field Display**:
   ```bash
   python3 ldap-u.py ldap_output.txt --level 3
   ```

## Example Output

```plaintext
Search Summary:
Including fields: accountExpires
Include-All fields: None
Excluding fields: testfield
Rare Standard Field Threshold Level: 1 (10%)
Users Shown: 6/21

User: Administrator
  Non-Standard Field: logonHours -> [': ////////////////////////////']
  Rare Standard Field: adminCount -> ['1']
  Non-Standard Field: lastLogonTimestamp -> ['133754595649786971']

--------------------------------------------------

User: support
  Non-Standard Field: info -> ['Ironside47pleasure40Watchful']
  Rare Standard Field: memberOf -> ['CN=Shared Support Accounts,CN=Users,DC=support,DC=htb', 'CN=Remote Management Users,CN=Builtin,DC=support,DC=htb']


--------------------------------------------------
```

## Notes

- Fields not typically found in LDAP data are highlighted as non-standard.
- Users with non-standard fields are displayed with red highlighting in `--list-users` mode.
- If a field or option is not recognized, the script displays a warning and continues processing.

## License

MIT License
