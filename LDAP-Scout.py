import re
import argparse
from collections import Counter
from colorama import Fore, Style, init
import sys

# Initialize colorama for cross-platform compatibility
init(autoreset=True)

# Set of standard LDAP attributes
standard_ldap_fields = {
    'dn', 'objectClass', 'cn', 'sn', 'givenName', 'distinguishedName', 'instanceType', 
    'whenCreated', 'whenChanged', 'displayName', 'uSNCreated', 'uSNChanged', 'name', 
    'objectGUID', 'userAccountControl', 'badPwdCount', 'codePage', 'countryCode', 
    'badPasswordTime', 'lastLogoff', 'lastLogon', 'pwdLastSet', 'primaryGroupID', 
    'objectSid', 'adminCount', 'accountExpires', 'logonCount', 'sAMAccountName', 
    'sAMAccountType', 'objectCategory', 'isCriticalSystemObject', 'dSCorePropagationData', 
    'telephoneNumber', 'mail', 'memberOf', 'description', 'title', 'department', 
    'company', 'streetAddress', 'postalCode', 'c', 'l', 'st'
}

# Thresholds mapping based on --level flag
threshold_levels = {
    1: 0.1,  # 10%
    2: 0.25, # 25%
    3: 0.5,  # 50%
    4: 0.75, # 75%
    5: 0.95  # 95%
}

def parse_ldap_output(ldap_output):
    users = []
    user = {}
    for line in ldap_output.splitlines():
        line = line.strip()
        if line == "":
            if user:
                users.append(user)
            user = {}
        elif ":" in line:
            key, value = map(str.strip, line.split(":", 1))
            if key in user:
                user[key].append(value)
            else:
                user[key] = [value]
        else:
            if user and list(user.keys())[-1]:
                last_key = list(user.keys())[-1]
                user[last_key][-1] += " " + line.strip()
    if user:
        users.append(user)
    return users

def list_fields(users):
    """Display a list of all fields found in LDAP data along with their occurrences."""
    field_count = Counter()
    for user in users:
        field_count.update(user.keys())
    
    total_users = len(users)

    print(f"\n{Fore.CYAN}List of all fields found and their occurrences:{Style.RESET_ALL}")
    for field, count in field_count.items():
        color = Fore.RED if field not in standard_ldap_fields else Fore.RESET
        print(f"{color}{field}: {count}/{total_users}{Style.RESET_ALL}")

def list_users(users, field_count):
    """Display a concise list of usernames, highlighting those with non-standard or rare fields."""
    total_users = len(users)
    print(f"\n{Fore.CYAN}List of all users with field types highlighted:{Style.RESET_ALL}")
    
    displayed_users = 0
    for user in users:
        username = user.get("cn", ["Unknown"])[0]
        
        # Skip 'Unknown' users from display and count
        if username == "Unknown":
            continue

        non_standard = any(field not in standard_ldap_fields for field in user)
        rare_field = any(field_count[field] < total_users * 0.6 for field in user)
        
        # Determine color based on field types
        if non_standard:
            color = Fore.RED
        elif rare_field:
            color = Fore.YELLOW
        else:
            color = Fore.RESET
        
        print(f"{color}{username}{Style.RESET_ALL}")
        displayed_users += 1

    # Update the displayed users count in summary
    return displayed_users

def validate_fields(fields, existing_fields):
    """Validates if specified fields exist in the LDAP data."""
    valid_fields = []
    for field in fields:
        if field in existing_fields:
            valid_fields.append(field)
        else:
            print(f"{Fore.RED}Warning: Field '{field}' does not exist in the LDAP data and will be ignored.{Style.RESET_ALL}")
    return valid_fields

def find_non_standard_fields(users, exclude_fields, include_fields, include_all_fields, threshold_level):
    threshold_percentage = threshold_levels[threshold_level]
    field_count = Counter()
    for user in users:
        field_count.update(user.keys())
    
    total_users = len(users)
    non_standard_fields_per_user = []

    # Keep track of all users with the fields specified in --include-all
    additional_include_users = []

    for user in users:
        username = user.get("cn", ["Unknown"])[0]
        if username == "Unknown" and 'description' not in user:
            continue
        
        non_standard_user_data = {}
        for field, value in user.items():
            # Filter based on threshold, exclude, and include criteria
            if field not in exclude_fields and (
                field not in standard_ldap_fields or field_count[field] < total_users * threshold_percentage
            ):
                label = "Non-Standard Field" if field not in standard_ldap_fields else "Rare Standard Field"
                color = Fore.MAGENTA if field not in standard_ldap_fields else Fore.YELLOW
                non_standard_user_data[field] = (label, color + field + Style.RESET_ALL, value)
        
        # Add included fields to existing results if they are present in the user
        if non_standard_user_data:
            # Only add specified --include fields if they are present in the user
            for include_field in include_fields:
                if include_field in user:
                    non_standard_user_data[include_field] = ("Included Field", Fore.GREEN + include_field + Style.RESET_ALL, user[include_field])
            non_standard_fields_per_user.append((username, non_standard_user_data))

        # Add users that match --include-all fields to the additional list if they contain those fields
        if include_all_fields and any(field in user for field in include_all_fields):
            include_all_user_data = {}
            for field in include_all_fields:
                if field in user:
                    include_all_user_data[field] = ("Include-All Field", Fore.GREEN + field + Style.RESET_ALL, user[field])
            additional_include_users.append((username, include_all_user_data))

    return non_standard_fields_per_user, additional_include_users

# Argument parsing
parser = argparse.ArgumentParser(
    description="Show non-standard LDAP fields from output.",
    epilog="Example LDAP search: ldapsearch -x -LLL -H ldap://<LDAP_SERVER> -D '<bind_dn>' -w <password> -b '<base_dn>' '(objectClass=user)' '*'"
)

parser.add_argument("input_file", help="Path to the LDAP output file.")
parser.add_argument(
    "--exclude", 
    nargs="+", 
    help="Fields to exclude from output. Use as '--exclude field1 field2' or '--exclude=field1,field2'.", 
    default=[]
)
parser.add_argument(
    "--include", 
    nargs="+", 
    help="Fields to include in output, adding them to users with non-standard data.", 
    default=[]
)
parser.add_argument(
    "--include-all", 
    nargs="+", 
    help="Show all users that have specified fields, in addition to the regular results.", 
    default=[]
)
parser.add_argument(
    "--list-fields",
    action="store_true",
    help="List all fields found in the LDAP data and their occurrence counts. Non-standard fields are shown in red."
)
parser.add_argument(
    "--list-users",
    action="store_true",
    help="List all users. Users with non-standard fields are shown in red; users with fields appearing in <60%% of entries are shown in yellow."
)
parser.add_argument(
    "--level", 
    type=int, 
    choices=[1, 2, 3, 4, 5], 
    default=2,  # Default level set to 2
    help="Control the %% threshold for showing standard fields (1 = 10%%, 5 = 95%%). Default is 2 (25%%)."
)

# Display help and exit if no arguments are provided
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args()

# Load LDAP output and parse exclusions and inclusions
with open(args.input_file, "r") as file:
    ldap_output = file.read()
exclude_fields = set(args.exclude)
include_fields = set(args.include)
include_all_fields = set(args.include_all)
threshold_level = args.level

# Parse the LDAP output
users = parse_ldap_output(ldap_output)
field_count = Counter(field for user in users for field in user.keys())

# Check and display fields if --list-fields is set
if args.list_fields:
    list_fields(users)
    sys.exit(0)

# Validate fields
all_fields_in_data = set(field_count.keys())
include_fields = validate_fields(include_fields, all_fields_in_data)
include_all_fields = validate_fields(include_all_fields, all_fields_in_data)

# Find non-standard fields and apply filtering criteria
if args.list_users:
    filtered_users_count = list_users(users, field_count)
else:
    non_standard_data, additional_include_users = find_non_standard_fields(users, exclude_fields, include_fields, include_all_fields, threshold_level)
    filtered_users_count = sum(1 for username, _ in non_standard_data if username != "Unknown")

# Show search summary with color if not in list-users mode
if not args.list_users:
    print(f"\n{Fore.CYAN}Search Summary:{Style.RESET_ALL}")
    if include_fields:
        print(f"{Fore.GREEN}Including fields: {', '.join(include_fields)}{Style.RESET_ALL}")
    if include_all_fields:
        print(f"{Fore.GREEN}Include-All fields: {', '.join(include_all_fields)}{Style.RESET_ALL}")
    if exclude_fields:
        print(f"{Fore.RED}Excluding fields: {', '.join(exclude_fields)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Rare Standard Field Threshold Level: {threshold_level} ({int(threshold_levels[threshold_level] * 100)}%)")
    print(f"{Fore.CYAN}Users Shown: {filtered_users_count}/{len(users) - sum(1 for user in users if user.get('cn', ['Unknown'])[0] == 'Unknown')}{Style.RESET_ALL}\n")

    # Display main filtered results
    for username, fields in non_standard_data:
        if username == "Unknown":
            continue  # Skip unknown users
        print(f"{Fore.CYAN}{Style.BRIGHT}User: {username}{Style.RESET_ALL}")
        for label, field, value in fields.values():
            print(f"  {Fore.YELLOW}{label}: {field}{Style.RESET_ALL} -> {Fore.GREEN}{value}{Style.RESET_ALL}")
        print(f"{Style.RESET_ALL}\n{'-'*50}\n")

    # Display users matching --include-all fields, if any
    if additional_include_users:
        print(f"{Fore.GREEN}{Style.BRIGHT}Additional Users with Include-All Fields:{Style.RESET_ALL}")
        for username, fields in additional_include_users:
            print(f"{Fore.CYAN}User: {username}{Style.RESET_ALL}")
            for label, field, value in fields.values():
                print(f"  {Fore.GREEN}{label}: {field}{Style.RESET_ALL} -> {Fore.GREEN}{value}{Style.RESET_ALL}")
            print(f"{Style.RESET_ALL}\n{'-'*50}\n")
