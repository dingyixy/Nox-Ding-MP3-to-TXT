import hashlib
import json
import os
from pathlib import Path


class Stopped(Exception):
    pass


def identity(path, model):
    path = Path(path).resolve()
    stat = path.stat()
    data = [str(path).casefold(), stat.st_size, stat.st_mtime_ns, model, 'zh-simplified-v1']
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()


def load_state(folder):
    try:
        value = json.loads((Path(folder) / '.transcribe-state.json').read_text('utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(folder, state):
    target = Path(folder) / '.transcribe-state.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, target)


def completed(folder, entry):
    if not isinstance(entry, dict):
        return False
    name = entry.get('name', '')
    return bool(name and Path(name).name == name and (Path(folder) / name).is_file())


def convert_one(model, source, folder, token, cancel, report, converter):
    source, folder = Path(source), Path(folder)
    # A distinct partial file preserves recognized text when interrupted.
    partial = folder / (source.stem[:100] + '.' + token[:12] + '.未完成.txt')
    if cancel.is_set():
        raise Stopped()
    segments, info = model.transcribe(str(source), language='zh', task='transcribe',
        beam_size=5, vad_filter=True, condition_on_previous_text=False)
    count = 0
    with partial.open('w', encoding='utf-8-sig') as output:
        for segment in segments:
            if cancel.is_set():
                raise Stopped()
            text = converter.convert(segment.text).strip()
            if text:
                output.write(text + '\n')
                output.flush()
                count += 1
            report(min(99, int(segment.end / max(info.duration, 0.01) * 100)))
    if cancel.is_set():
        raise Stopped()
    if not count:
        raise ValueError('未识别出语音，未生成完成文件；请检查音频或更换模型')
    base = source.stem[:140]
    for number in range(10000):
        name = base + ('' if number == 0 else '_转写' + str(number)) + '.txt'
        target = folder / name
        try:
            with target.open('x', encoding='utf-8-sig') as output:
                output.write(partial.read_text('utf-8-sig'))
            partial.unlink()
            report(100)
            return name
        except FileExistsError:
            continue
    raise OSError('同名文件过多，请更换输出目录')
