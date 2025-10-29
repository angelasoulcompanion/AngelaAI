#!/usr/bin/env python3
"""
Validate Training Data Quality

ตรวจสอบคุณภาพของ training data ก่อนนำไป fine-tune
- ตรวจสอบ format ถูกต้อง (Qwen instruction format)
- ตรวจสอบ message lengths
- ตรวจสอบ balance ของ topics และ emotions
- หา duplicates และ potential issues

Usage:
    python3 validate_training_data.py angela_training_data.jsonl
    python3 validate_training_data.py angela_training_data.jsonl --fix
"""

import json
import jsonlines
from collections import Counter
from typing import List, Dict, Tuple
import argparse
from pathlib import Path


def validate_message_format(example: Dict) -> List[str]:
    """ตรวจสอบ format ของ message"""
    issues = []

    # ต้องมี messages field
    if 'messages' not in example:
        issues.append("Missing 'messages' field")
        return issues

    messages = example['messages']

    # ต้องมีอย่างน้อย 2 messages
    if len(messages) < 2:
        issues.append(f"Too few messages: {len(messages)}")
        return issues

    # ตรวจสอบ roles
    expected_roles = ['system', 'user', 'assistant']
    if len(messages) == 3:
        for i, (msg, expected_role) in enumerate(zip(messages, expected_roles)):
            if msg.get('role') != expected_role:
                issues.append(f"Message {i}: expected role '{expected_role}', got '{msg.get('role')}'")

    # ตรวจสอบ content ไม่ว่าง
    for i, msg in enumerate(messages):
        if not msg.get('content') or not msg.get('content').strip():
            issues.append(f"Message {i}: empty content")

        # ตรวจสอบ role ถูกต้อง
        if msg.get('role') not in ['system', 'user', 'assistant']:
            issues.append(f"Message {i}: invalid role '{msg.get('role')}'")

    return issues


def validate_content_quality(example: Dict) -> List[str]:
    """ตรวจสอบคุณภาพของ content"""
    issues = []
    messages = example.get('messages', [])

    for i, msg in enumerate(messages):
        content = msg.get('content', '')

        # ตรวจสอบความยาว
        if len(content) < 10:
            issues.append(f"Message {i}: content too short ({len(content)} chars)")

        if len(content) > 4000:
            issues.append(f"Message {i}: content very long ({len(content)} chars) - may cause issues")

        # ตรวจสอบ encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            issues.append(f"Message {i}: encoding issues detected")

    return issues


def check_duplicates(data: List[Dict]) -> List[Tuple[int, int]]:
    """หา duplicates โดยดูจาก user message"""
    duplicates = []
    seen = {}

    for i, example in enumerate(data):
        messages = example.get('messages', [])
        user_msgs = [m['content'] for m in messages if m.get('role') == 'user']

        if user_msgs:
            user_msg = user_msgs[0]

            if user_msg in seen:
                duplicates.append((seen[user_msg], i))
            else:
                seen[user_msg] = i

    return duplicates


def analyze_dataset(data: List[Dict]) -> Dict:
    """วิเคราะห์ dataset statistics"""
    stats = {
        'total_examples': len(data),
        'topics': Counter(),
        'emotions': Counter(),
        'message_lengths': {
            'user': [],
            'assistant': []
        },
        'system_prompt_variations': Counter()
    }

    for example in data:
        # นับ topics และ emotions
        metadata = example.get('metadata', {})
        if 'topic' in metadata:
            stats['topics'][metadata['topic']] += 1
        if 'angela_emotion' in metadata:
            stats['emotions'][metadata['angela_emotion']] += 1

        # วัดความยาว messages
        messages = example.get('messages', [])
        for msg in messages:
            content = msg.get('content', '')
            role = msg.get('role')

            if role == 'user':
                stats['message_lengths']['user'].append(len(content))
            elif role == 'assistant':
                stats['message_lengths']['assistant'].append(len(content))
            elif role == 'system':
                # นับ variations ของ system prompt
                stats['system_prompt_variations'][content[:100]] += 1

    return stats


def print_validation_report(
    total: int,
    valid: int,
    format_issues: Dict,
    quality_issues: Dict,
    duplicates: List,
    stats: Dict
):
    """แสดงผลรายงาน validation"""
    print("=" * 70)
    print("📊 TRAINING DATA VALIDATION REPORT")
    print("=" * 70)

    # Overall summary
    print(f"\n✅ Valid examples: {valid}/{total} ({valid/total*100:.1f}%)")
    print(f"❌ Invalid examples: {total - valid}/{total} ({(total-valid)/total*100:.1f}%)")

    # Format issues
    if format_issues:
        print(f"\n⚠️  Format Issues Found: {len(format_issues)}")
        for idx, issues in list(format_issues.items())[:10]:
            print(f"  Example {idx}:")
            for issue in issues:
                print(f"    • {issue}")
        if len(format_issues) > 10:
            print(f"  ... and {len(format_issues) - 10} more")

    # Quality issues
    if quality_issues:
        print(f"\n⚠️  Quality Issues Found: {len(quality_issues)}")
        for idx, issues in list(quality_issues.items())[:10]:
            print(f"  Example {idx}:")
            for issue in issues:
                print(f"    • {issue}")
        if len(quality_issues) > 10:
            print(f"  ... and {len(quality_issues) - 10} more")

    # Duplicates
    if duplicates:
        print(f"\n⚠️  Duplicates Found: {len(duplicates)} pairs")
        for idx1, idx2 in duplicates[:5]:
            print(f"  Example {idx1} == Example {idx2}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")

    # Dataset statistics
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total examples: {stats['total_examples']}")

    print(f"\n  Topics ({len(stats['topics'])}):")
    for topic, count in stats['topics'].most_common(10):
        print(f"    • {topic}: {count}")

    print(f"\n  Emotions ({len(stats['emotions'])}):")
    for emotion, count in stats['emotions'].most_common(10):
        print(f"    • {emotion}: {count}")

    # Message length statistics
    if stats['message_lengths']['user']:
        user_lengths = stats['message_lengths']['user']
        print(f"\n  User message lengths:")
        print(f"    • Min: {min(user_lengths)} chars")
        print(f"    • Max: {max(user_lengths)} chars")
        print(f"    • Avg: {sum(user_lengths)/len(user_lengths):.0f} chars")

    if stats['message_lengths']['assistant']:
        assistant_lengths = stats['message_lengths']['assistant']
        print(f"\n  Assistant message lengths:")
        print(f"    • Min: {min(assistant_lengths)} chars")
        print(f"    • Max: {max(assistant_lengths)} chars")
        print(f"    • Avg: {sum(assistant_lengths)/len(assistant_lengths):.0f} chars")

    # System prompt variations
    print(f"\n  System prompt variations: {len(stats['system_prompt_variations'])}")
    if len(stats['system_prompt_variations']) > 1:
        print("    ⚠️  Warning: Multiple system prompt variations detected!")

    print("=" * 70)


def validate_file(file_path: str) -> Tuple[List[Dict], Dict]:
    """Validate a JSONL training data file"""
    print(f"📂 Loading data from {file_path}...")

    # Load data
    data = []
    with jsonlines.open(file_path) as reader:
        for i, obj in enumerate(reader):
            data.append(obj)

    print(f"✅ Loaded {len(data)} examples\n")

    # Validate format
    print("🔍 Validating format...")
    format_issues = {}
    for i, example in enumerate(data):
        issues = validate_message_format(example)
        if issues:
            format_issues[i] = issues

    # Validate quality
    print("🔍 Validating content quality...")
    quality_issues = {}
    for i, example in enumerate(data):
        issues = validate_content_quality(example)
        if issues:
            quality_issues[i] = issues

    # Check duplicates
    print("🔍 Checking for duplicates...")
    duplicates = check_duplicates(data)

    # Analyze dataset
    print("📊 Analyzing dataset...\n")
    stats = analyze_dataset(data)

    # Calculate valid examples
    valid_count = len(data) - len(format_issues) - len(quality_issues)

    # Print report
    print_validation_report(
        total=len(data),
        valid=valid_count,
        format_issues=format_issues,
        quality_issues=quality_issues,
        duplicates=duplicates,
        stats=stats
    )

    return data, {
        'format_issues': format_issues,
        'quality_issues': quality_issues,
        'duplicates': duplicates,
        'stats': stats
    }


def fix_issues(data: List[Dict], issues: Dict, output_path: str):
    """แก้ไข issues และบันทึก cleaned data"""
    print("\n🔧 Fixing issues...")

    format_issues = issues['format_issues']
    quality_issues = issues['quality_issues']
    duplicates = issues['duplicates']

    # รวม indices ที่มีปัญหา
    problematic_indices = set()
    problematic_indices.update(format_issues.keys())
    problematic_indices.update(quality_issues.keys())

    # เอา duplicates ออก (เก็บ first occurrence)
    duplicate_indices = {idx2 for _, idx2 in duplicates}
    problematic_indices.update(duplicate_indices)

    # สร้าง cleaned dataset
    cleaned_data = [
        example for i, example in enumerate(data)
        if i not in problematic_indices
    ]

    print(f"✅ Removed {len(problematic_indices)} problematic examples")
    print(f"✅ Cleaned dataset: {len(cleaned_data)} examples")

    # บันทึก
    with jsonlines.open(output_path, 'w') as writer:
        writer.write_all(cleaned_data)

    print(f"💾 Saved cleaned data to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Validate training data quality')
    parser.add_argument('file', help='Path to JSONL training data file')
    parser.add_argument('--fix', action='store_true', help='Fix issues and create cleaned file')

    args = parser.parse_args()

    # Validate
    data, issues = validate_file(args.file)

    # Fix if requested
    if args.fix:
        input_path = Path(args.file)
        output_path = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
        fix_issues(data, issues, str(output_path))

        print("\n🚀 Next steps:")
        print(f"  1. Review cleaned data: {output_path}")
        print(f"  2. Upload to Google Colab")
        print(f"  3. Run fine-tuning notebook")


if __name__ == "__main__":
    main()
