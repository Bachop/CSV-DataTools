"""计算相关的纯函数，供 GUI 层调用。"""
import csv
import numpy as np
import os
from typing import Dict, Any, List, Optional


def compute_stats_from_selection(data: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
	"""基于 `get_selected_data()` 返回的数据计算每列的统计量（均值、峰峰值、点数）。

	返回格式: {col_index: {'label': str, 'mean': float, 'peak': float, 'count': int}, ...}
	"""
	results = {}
	for col, values in data.items():
		y = np.array(values.get('y_data', []), dtype=float)
		if y.size == 0:
			continue
		mean = float(np.mean(y))
		peak = float(np.max(y) - np.min(y))
		results[col] = {
			'label': values.get('label', ''),
			'mean': mean,
			'peak': peak,
			'count': int(y.size)
		}
	return results


def compute_diffs(col1_values: List[str], col2_values: List[str]) -> List[Optional[float]]:
	"""计算两列对应行的差值（col1 - col2）。

	非数值或缺失返回 None，以便上层决定如何显示/写入。
	"""
	max_len = max(len(col1_values), len(col2_values))
	diffs: List[Optional[float]] = []
	for i in range(max_len):
		v1 = col1_values[i] if i < len(col1_values) else ''
		v2 = col2_values[i] if i < len(col2_values) else ''
		try:
			if v1 is None or v2 is None:
				diffs.append(None)
				continue
			if isinstance(v1, str):
				v1 = v1.strip()
			if isinstance(v2, str):
				v2 = v2.strip()
			if v1 == '' or v2 == '':
				diffs.append(None)
				continue
			f1 = float(v1)
			f2 = float(v2)
			diffs.append(f1 - f2)
		except (ValueError, TypeError):
			diffs.append(None)
	return diffs


def read_csv_columns_for_batch(file_path: str, selected_columns: Dict[int, str], encoding: str = 'utf-8') -> Optional[Dict[int, Dict[str, Any]]]:
	"""从 CSV 文件中读取选定列的数据，返回与 DataViewer.read_csv_for_batch 类似的结构。

	`selected_columns` 是一个 mapping: 原始列索引 -> 列名（label），用于匹配表头。
	返回 None 表示未找到有效数据。
	"""
	try:
		with open(file_path, 'r', newline='', encoding=encoding, errors='replace') as f:
			reader = csv.reader(f)
			data = list(reader)

			if not data:
				return None

			header_row = data[0] if data else []

			# 找到匹配的列索引
			column_indices = {}
			for col_index, header in enumerate(header_row):
				for orig_col, col_name in selected_columns.items():
					if header == col_name:
						column_indices[col_index] = col_name
						break

			if not column_indices:
				return None

			columns: Dict[int, Dict[str, Any]] = {}
			for col_index, col_name in column_indices.items():
				columns[col_index] = {'x_data': [], 'y_data': [], 'label': col_name}

			for row_index, row in enumerate(data[1:], start=1):
				for col_index in column_indices:
					if col_index < len(row):
						try:
							y_val = float(row[col_index])
							columns[col_index]['x_data'].append(row_index)
							columns[col_index]['y_data'].append(y_val)
						except (ValueError, TypeError):
							pass

			valid_columns = {col: d for col, d in columns.items() if d['y_data']}
			return valid_columns if valid_columns else None
	except Exception:
		return None


def compute_batch_all_results(current_file_path: str, current_data: Dict[int, Dict[str, Any]], other_file_paths: List[str], selected_columns: Dict[int, str], encoding: str = 'utf-8') -> Dict[str, Any]:
	"""计算批量统计量结果。

	返回结构与原来 data_viewer 中构建的 all_results 兼容：
	{
		'column_names': [label,...],
		'files': [ {'name': filename, 'results': {label: {'mean':..,'peak':..}}}, ... ]
	}
	"""
	all_results: Dict[str, Any] = {
		'column_names': [values['label'] for values in current_data.values()],
		'files': []
	}

	# 当前文件
	current_file_results = {}
	stats = compute_stats_from_selection(current_data)
	for col_idx, info in stats.items():
		label = info.get('label', '')
		current_file_results[label] = {'mean': info['mean'], 'peak': info['peak']}

	all_results['files'].append({'name': os.path.basename(current_file_path), 'results': current_file_results})

	# 其他文件
	for fp in other_file_paths:
		try:
			file_data = read_csv_columns_for_batch(fp, selected_columns, encoding=encoding)
			if file_data is None:
				continue
			file_stats = compute_stats_from_selection(file_data)
			file_results = {}
			for _, info in file_stats.items():
				label = info.get('label', '')
				file_results[label] = {'mean': info['mean'], 'peak': info['peak']}
			all_results['files'].append({'name': os.path.basename(fp), 'results': file_results})
		except Exception:
			continue

	return all_results

