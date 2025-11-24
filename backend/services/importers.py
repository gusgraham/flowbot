import os
import re
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


# --- Helper Functions (Ported from flowbot_helper.py) ---

def parse_format_token(token):
    token = token.strip()
    if token.startswith('[') and token.endswith(']'):
        return ('repeat', int(token.strip('[]')))
    
    m_skip = re.match(r'^(\d+)X$', token)
    if m_skip:
        return ('skip', int(m_skip.group(1)), 1)
    
    m = re.match(r'^(\d+)([A-Z].*)$', token)
    if m:
        rep = int(m.group(1))
        rest = m.group(2)
        if rest.startswith('I'):
            m2 = re.match(r'^I(\d+)$', rest)
            if m2:
                width = int(m2.group(1))
                return ('int', width, rep)
        elif rest.startswith('F'):
            m2 = re.match(r'^F(\d+)\.(\d+)$', rest)
            if m2:
                width = int(m2.group(1))
                decimals = int(m2.group(2))
                return ('float', width, decimals, rep)
        elif rest.startswith('A'):
            m2 = re.match(r'^A(\d+)$', rest)
            if m2:
                width = int(m2.group(1))
                return ('string', width, rep)
        elif rest.startswith('D'):
            m2 = re.match(r'^D(\d+)$', rest)
            if m2:
                width = int(m2.group(1))
                return ('date', width, rep)
        raise ValueError("Unknown format token: " + token)
    
    m = re.match(r'^I(\d+)$', token)
    if m:
        return ('int', int(m.group(1)), 1)
    m = re.match(r'^F(\d+)(?:\.(\d+))?$', token)    
    if m:
        return ('float', int(m.group(1)), int(m.group(2) or 0), 1)    
    m = re.match(r'^A(\d+)$', token)
    if m:
        return ('string', int(m.group(1)), 1)
    m = re.match(r'^D(\d+)$', token)
    if m:
        return ('date', int(m.group(1)), 1)
    
    raise ValueError("Unknown format token: " + token)

def parse_fixed_width(text, format_tokens):
    pos = 0
    results = []
    for token in format_tokens:
        token_info = parse_format_token(token)
        typ = token_info[0]
        if typ == 'repeat':
            continue
        rep = token_info[-1]
        for _ in range(rep):
            width = token_info[1]
            segment = text[pos:pos+width]
            pos += width
            if typ == 'int':
                try:
                    results.append(int(segment.strip()))
                except ValueError:
                    results.append(None)
            elif typ == 'float':
                try:
                    results.append(float(segment.strip()))
                except ValueError:
                    results.append(None)
            elif typ in ('string', 'date'):
                results.append(segment.strip())
            elif typ == 'skip':
                continue
    return results

def split_format_tokens(tokens):
    groups = []
    current_group = []
    for token in tokens:
        if '/' in token:
            parts = token.split('/')
            if parts[0]:
                current_group.append(parts[0])
            groups.append(current_group)
            for mid in parts[1:-1]:
                if mid:
                    groups.append([mid])
            current_group = []
            if parts[-1]:
                current_group.append(parts[-1])
        else:
            current_group.append(token)
    if current_group:
        groups.append(current_group)
    return groups

def parse_constants(const_lines, c_format, constants_names):
    tokens = [tok.strip() for tok in c_format.split(",") if tok.strip()]
    if tokens and tokens[0].isdigit():
        i_tokens = int(tokens[0])
        tokens = tokens[1:]

    token_groups = split_format_tokens(tokens)
    const_data_lines = [line.rstrip("\n") for line in const_lines if line.strip()]
    
    # if len(const_data_lines) < len(token_groups):
    #     raise ValueError("Not enough constant data lines to match C_FORMAT groups.")

    values = []
    token_count = 0
    has_rg_id = False
    rg_id = ""
    
    for i, token_group in enumerate(token_groups):
        if i >= len(const_data_lines):
             break
        line_text = const_data_lines[i]
        
        # Logic to handle RG ID appended to end
        original_token_group = list(token_group)
        for token in token_group:
            token_count += 1
            if token_count > i_tokens:
                has_rg_id = True
                rg_id = token_group[-1]
                token_group.pop()
                break
        
        group_values = parse_fixed_width(line_text, token_group)
        values.extend(group_values)

    names_tokens = [tok.strip() for tok in constants_names.split(",") if tok.strip()]
    if names_tokens and names_tokens[0].isdigit():
        names_tokens = names_tokens[1:]

    if has_rg_id:
        names_tokens.append("RAINGAUGE")
        values.append(rg_id)

    # if len(names_tokens) != len(values):
    #     raise ValueError(f"Warning: Number of constant names and parsed values do not match.")

    constants = dict(zip(names_tokens, values))
    return constants

def parse_header(lines):
    header = {}
    current_key = None
    for line in lines:
        line = line.rstrip('\n')
        if line.startswith('**'):
            parts = line.split(':', 1)
            if len(parts) < 2:
                continue
            key = parts[0].lstrip('*').strip()
            value = parts[1].strip()
            header[key] = value
            current_key = key
        elif line.startswith('*+'):
            if current_key:
                continuation = line[2:].strip()
                if current_key in ['CONSTANTS', 'FIELD', 'UNITS', 'FORMAT', 'C_UNITS', 'C_FORMAT', 'RECORD_LENGTH']:
                    if not header[current_key].strip().endswith(','):
                         header[current_key] += "," + continuation
                    else:
                         header[current_key] += continuation
                else:
                    header[current_key] += " " + continuation
        elif line.startswith('*CSTART'):
            break
    return header

def parse_payload(payload_lines, record_format, record_length, field_names):
    tokens = [tok.strip() for tok in record_format.split(',') if tok.strip()]
    tokens.pop(0)
    repeat_token = tokens.pop(-1)
    # repeat_count = int(repeat_token.strip('[]'))
    unit_format_tokens = tokens
    fields = [f.strip() for f in field_names.split(',')]

    # Estimate unit width if record_length is available
    # unit_width = record_length // repeat_count
    
    records = []
    for line in payload_lines:
        line = line.rstrip('\n')
        if line.startswith('*END'):
            break
        if not line.strip():
            continue
        
        # Simplified parsing: assume fixed width based on format tokens
        # We need to calculate unit width from tokens
        unit_width = 0
        for token in unit_format_tokens:
             info = parse_format_token(token)
             if info[0] != 'repeat':
                 unit_width += info[1] * info[-1]
        
        if unit_width == 0:
            continue

        record = []
        max_units = len(line) // unit_width
        for i in range(max_units):
            unit_text = line[i * unit_width:(i + 1) * unit_width]
            values = parse_fixed_width(unit_text, unit_format_tokens)
            unit_data = dict(zip(fields, values))
            record.append(unit_data)
        if record:
            records.append(record)
    return records

def parse_date(date_str: str) -> datetime:
    if not isinstance(date_str, str):
        return date_str # Already datetime?
        
    date_str = date_str.strip()
    if len(date_str) == 10:
        return datetime.strptime(date_str, "%y%m%d%H%M")
    elif len(date_str) == 12:
        return datetime.strptime(date_str, "%Y%m%d%H%M")
    else:
        # Try ISO format or other fallbacks
        try:
            return datetime.fromisoformat(date_str)
        except:
            raise ValueError("Unsupported date format: " + date_str)

def fill_payload_gap(parsed_payload, missing_steps, unit_template):
    if not unit_template:
        return []

    repeat_count = len(unit_template)
    field_list = list(unit_template[0].keys())
    blank_units = [dict.fromkeys(field_list, None) for _ in range(missing_steps)]
    flat_parsed_units = [unit for record in parsed_payload for unit in record]
    all_units = blank_units + flat_parsed_units

    new_payload = []
    while all_units:
        record = all_units[:repeat_count]
        new_payload.append(record)
        all_units = all_units[repeat_count:]
    return new_payload

def format_value(token_info, value):
    typ = token_info[0]
    width = token_info[1]
    if value is None:
        return " " * width
    if typ == 'int':
        return str(int(value)).rjust(width)
    elif typ == 'float':
        decimals = token_info[2]
        fmt = f"{{:>{width}.{decimals}f}}"
        return fmt.format(float(value))
    elif typ == 'string':
        s = str(value)
        return s.ljust(width)[:width]
    elif typ == 'date':
        if width == 10:
            return value.strftime("%y%m%d%H%M")
        elif width == 12:
            return value.strftime("%Y%m%d%H%M")
        else:
            return value.strftime("%Y%m%d%H%M")[:width].ljust(width)
    elif typ == 'skip':
        return " " * width
    return " " * width

def parse_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    header_lines = []
    data_blocks = []
    current_constants = []
    current_payload = []

    in_header = True
    in_constants = False
    in_payload = False

    for line in lines:
        if line.startswith('*CSTART'):
            in_constants = True
            in_payload = False
            current_constants = []
            continue
        elif line.startswith('*CEND'):
            in_constants = False
            in_payload = True
            current_payload = []
            continue
        elif line.startswith('*$') or line.startswith('*END'):
            in_payload = False
            if current_constants and current_payload:
                data_blocks.append((current_constants, current_payload))
            current_constants = []
            current_payload = []
            continue
        elif in_constants:
            current_constants.append(line)
        elif in_payload:
            current_payload.append(line)
        elif in_header:
            header_lines.append(line)

    if current_constants and current_payload:
        data_blocks.append((current_constants, current_payload))

    header = parse_header(header_lines)
    
    data_format = header.get('DATA_FORMAT', '')
    identifier = header.get('IDENTIFIER', '')
    field_line = header.get('FIELD', '')
    field_tokens = [tok.strip() for tok in field_line.split(',') if tok.strip()]
    if field_tokens and field_tokens[0].isdigit():
        field_names = ",".join(field_tokens[1:])
    else:
        field_names = ",".join(field_tokens)

    record_line = header.get('RECORD_LENGTH', '')
    record_length = None
    if record_line:
        parts = [p.strip() for p in record_line.split(',')]
        if len(parts) >= 2:
            record_length = int(parts[1])

    record_format = header.get('FORMAT', '')
    constants_line = header.get('CONSTANTS', '')
    constants_tokens = [tok.strip() for tok in constants_line.split(',') if tok.strip()]
    if constants_tokens and constants_tokens[0].isdigit():
        constants_names = ",".join(constants_tokens[1:])
    else:
        constants_names = ",".join(constants_tokens)

    c_format = header.get('C_FORMAT', '')

    full_payload = []
    constants = {}
    blocks = []
    previous_end = None

    for idx, (const_lines, payload_lines) in enumerate(data_blocks):
        parsed_constants = parse_constants(const_lines, c_format, constants_names)
        start_dt = parse_date(parsed_constants["START"])
        # end_dt = parse_date(parsed_constants["END"])
        interval_minutes = int(parsed_constants["INTERVAL"])

        parsed_payload = parse_payload(payload_lines, record_format, record_length, field_names)

        if previous_end is not None:
            expected_start = previous_end + timedelta(minutes=interval_minutes)
            if start_dt > expected_start:
                gap_minutes = int((start_dt - expected_start).total_seconds() / 60)
                missing_steps = gap_minutes // interval_minutes
                
                if parsed_payload:
                    unit_template = parsed_payload[0]
                    parsed_payload = fill_payload_gap(parsed_payload, missing_steps, unit_template)
                    parsed_constants["START"] = expected_start # Update start date

        blocks.append({'constants': parsed_constants, 'payload': parsed_payload})
        full_payload.extend(parsed_payload)
        if idx == 0:
            constants = parsed_constants
        previous_end = parse_date(parsed_constants["END"])

    if blocks:
        last_constants = blocks[-1]['constants']
        if 'END' in last_constants:
            constants['END'] = last_constants['END']

    return {
        'header': header,
        'constants': constants,
        'payload': full_payload,
        'blocks': blocks,
        'data_format': data_format,
        'identifier': identifier
    }

# --- Importer Functions (Ported from flowbot_monitors.py) ---

def import_fdv_file(file_path: str) -> Dict[str, Any]:
    """
    Imports an FDV/STD file and returns a dictionary with flow monitor data.
    """
    try:
        file_data = parse_file(file_path)
        all_units = [unit for record in file_data["payload"] for unit in record]
        
        constants = file_data["constants"]
        start_dt = parse_date(constants["START"])
        end_dt = parse_date(constants["END"])
        interval_minutes = int(constants["INTERVAL"])
        interval = timedelta(minutes=interval_minutes)
        
        date_range = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_range.append(current_dt)
            current_dt += interval
            
        duration_mins = (end_dt - start_dt).total_seconds() / 60
        no_of_records = int(duration_mins / interval_minutes) + 1
        
        flow_data = []
        depth_data = []
        velocity_data = []
        
        i_record = 0
        for unit in all_units:
            i_record += 1
            if i_record <= no_of_records:
                flow_data.append(float(unit.get("FLOW", 0.0) or 0.0))
                depth_data.append(float(unit.get("DEPTH", 0.0) or 0.0))
                velocity_data.append(float(unit.get("VELOCITY", 0.0) or 0.0))
                
        monitor_name = "Unknown"
        record_line = file_data['header'].get('IDENTIFIER', '')
        if record_line:
            parts = [p.strip() for p in record_line.split(',')]
            if len(parts) >= 2:
                monitor_name = parts[1]
                
        flow_units = ""
        depth_units = ""
        velocity_units = ""
        record_line = file_data['header'].get('UNITS', '')
        if record_line:
            parts = [p.strip() for p in record_line.split(',')]
            if len(parts) >= 4:
                flow_units = f'Flow {parts[1]}'
                depth_units = f'Depth {parts[2]}'
                velocity_units = f'Velocity {parts[3]}'
                
        rain_gauge_name = constants.get('RAINGAUGE', '')
        
        return {
            "name": monitor_name,
            "type": "flow_monitor",
            "interval_minutes": interval_minutes,
            "start_time": start_dt,
            "end_time": end_dt,
            "units": {
                "flow": flow_units,
                "depth": depth_units,
                "velocity": velocity_units
            },
            "rain_gauge_name": rain_gauge_name,
            "data": {
                "time": date_range,
                "flow": flow_data,
                "depth": depth_data,
                "velocity": velocity_data
            }
        }
    except Exception as e:
        raise ValueError(f"Error parsing FDV file {os.path.basename(file_path)}: {str(e)}")

def import_r_file(file_path: str) -> Dict[str, Any]:
    """
    Imports an R/STD file and returns a dictionary with rain gauge data.
    """
    try:
        file_data = parse_file(file_path)
        all_units = [unit for record in file_data["payload"] for unit in record]
        
        constants = file_data["constants"]
        start_dt = parse_date(constants["START"])
        end_dt = parse_date(constants["END"])
        interval_minutes = int(constants["INTERVAL"])
        interval = timedelta(minutes=interval_minutes)
        
        date_range = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_range.append(current_dt)
            current_dt += interval
            
        duration_mins = (end_dt - start_dt).total_seconds() / 60
        no_of_records = int(duration_mins / interval_minutes) + 1
        
        rainfall_data = []
        i_record = 0
        for unit in all_units:
            i_record += 1
            if i_record <= no_of_records:
                rainfall_data.append(float(unit.get("INTENSITY", 0.0) or 0.0))
                
        gauge_name = "Unknown"
        record_line = file_data['header'].get('IDENTIFIER', '')
        if record_line:
            parts = [p.strip() for p in record_line.split(',')]
            if len(parts) >= 2:
                gauge_name = parts[1]
                
        return {
            "name": gauge_name,
            "type": "rain_gauge",
            "interval_minutes": interval_minutes,
            "start_time": start_dt,
            "end_time": end_dt,
            "data": {
                "time": date_range,
                "rainfall": rainfall_data
            }
        }
    except Exception as e:
        raise ValueError(f"Error parsing R file {os.path.basename(file_path)}: {str(e)}")
