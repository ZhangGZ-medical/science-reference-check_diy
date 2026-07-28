#!/usr/bin/env python3
"""
science-reference-check_diy — 科学引文预校验与格式解析工具

功能：
1. 从文本中解析参考文献列表（支持 GB/T 7714、Vancouver、自由格式）
2. 提取每条引文的字段（作者、标题、期刊、年份、卷期页码）
3. 执行格式层面的预校验（字段完整性、特殊字符检查）
4. 按文献类型分组（期刊/专利/临床试验/预印本/其他）
5. 生成验证 Agent 的分组配置

用法：
    python verify_refs.py <input_file> [--format gb|vancouver|auto] [--output json|text]
    python verify_refs.py --stdin [--format auto] [--output json]
"""

import re
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class CitationType(Enum):
    JOURNAL = "journal"           # 期刊论文
    PATENT_CN = "patent_cn"       # 中国专利
    PATENT_INTL = "patent_intl"   # 国际专利
    CLINICAL_TRIAL = "trial"      # 临床试验
    PREPRINT = "preprint"         # 预印本
    CONFERENCE = "conference"     # 会议论文
    BOOK = "book"                 # 书籍
    WEB = "web"                   # 网页/报告
    UNKNOWN = "unknown"           # 无法识别


@dataclass
class Citation:
    """单条引文的数据结构"""
    number: int                    # 编号
    raw_text: str                  # 原始文本
    ref_type: CitationType = CitationType.UNKNOWN

    # 核心字段
    authors: str = ""              # 作者列表
    title: str = ""                # 标题
    journal: str = ""              # 期刊/来源
    year: str = ""                 # 年份
    volume: str = ""               # 卷
    issue: str = ""                # 期
    pages: str = ""                # 页码
    doi: str = ""                  # DOI
    pmid: str = ""                 # PMID

    # 扩展字段（专利/临床试验等）
    patent_number: str = ""        # 专利号
    application_date: str = ""     # 申请日
    publication_date: str = ""     # 公开/出版日
    trial_id: str = ""             # 临床试验备案号
    institution: str = ""          # 机构
    url: str = ""                  # URL

    # 校验状态
    issues: list = field(default_factory=list)  # 格式问题列表


class ReferenceParser:
    """参考文献解析器"""

    # === 期刊论文正则 ===
    # GB/T 7714 格式: 作者. 标题[J]. 期刊, 年, 卷(期): 页码.
    RE_GB_JOURNAL = re.compile(
        r'(?P<authors>.+?)\.\s*'
        r'(?P<title>.+?)\.\s*'
        r'(?P<journal>.+?),\s*'
        r'(?P<year>\d{4})'
        r'(?:,\s*(?P<vol>\d+)\s*(?:\((?P<issue>[\d\-]+)\))?)?'
        r'(?::\s*(?P<pages>[^\.]+))?\.?',
        re.DOTALL
    )

    # Vancouver 格式: 作者. 标题. 期刊. 年;卷(期):页码.
    RE_VANCOUVER = re.compile(
        r'(?P<authors>.+?)\.\s*'
        r'(?P<title>.+?)\.\s*'
        r'(?P<journal>.+?)\.\s*'
        r'(?P<year>\d{4});?'
        r'(?P<vol>\d+)?\(?(?P<issue>[\d\-]+)?\)?'
        r'(?::(?P<pages>[^\.]+))?\.?',
        re.DOTALL
    )

    # 专利号识别
    RE_PATENT_CN = re.compile(r'CN\s*(\d{7,12})\s*[ABU]?', re.IGNORECASE)
    RE_PATENT_INTL = re.compile(r'(?:US|WO|EP|JP|KR)\s*\d{4,}/\d{4,}', re.IGNORECASE)

    # 临床试验备案号
    RE_TRIAL_CN = re.compile(r'MR\s*-\s*\d{2}\s*-\s*\d{2}\s*-\s*\d{6}')
    RE_TRIAL_NCT = re.compile(r'NCT\s*\d{8}')

    # 预印本标识
    RE_PREPRINT = re.compile(r'(?:arXiv|bioRxiv|medRxiv|ChemRxiv)',
                             re.IGNORECASE)

    # DOI
    RE_DOI = re.compile(r'10\.\d{4,}/[^\s]+')

    # PMID
    RE_PMID = re.compile(r'PMID[:\s]*(\d{7,8})', re.IGNORECASE)

    @classmethod
    def parse_text(cls, text: str) -> list[Citation]:
        """从文本中解析所有参考文献"""
        citations = []

        # 按 [N] 或 N. 分段
        blocks = cls._split_into_blocks(text)

        for num, block in blocks:
            citation = cls._parse_single(num, block)
            cls._pre_validate(citation)
            citations.append(citation)

        return citations

    @classmethod
    def _split_into_blocks(cls, text: str) -> list[tuple[int, str]]:
        """将文本按编号分段"""
        pattern = re.compile(
            r'(?:^|\n)\s*\[(\d+)\]\s+', re.MULTILINE
        )
        blocks = []
        matches = list(pattern.finditer(text))

        for i, match in enumerate(matches):
            num = int(match.group(1))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            blocks.append((num, content))

        return blocks

    @classmethod
    def _parse_single(cls, num: int, text: str) -> Citation:
        """解析单条引文"""
        citation = Citation(number=num, raw_text=text.strip())

        # 检测文献类型
        citation.ref_type = cls._detect_type(text)

        # 提取 DOI 和 PMID
        doi_match = cls.RE_DOI.search(text)
        if doi_match:
            citation.doi = doi_match.group()

        pmid_match = cls.RE_PMID.search(text)
        if pmid_match:
            citation.pmid = pmid_match.group(1)

        # 按类型解析
        if citation.ref_type in [CitationType.PATENT_CN,
                                  CitationType.PATENT_INTL]:
            cls._parse_patent(citation, text)
        elif citation.ref_type == CitationType.CLINICAL_TRIAL:
            cls._parse_trial(citation, text)
        elif citation.ref_type == CitationType.PREPRINT:
            cls._parse_journal_like(citation, text)
        else:
            cls._parse_journal_like(citation, text)

        return citation

    @classmethod
    def _detect_type(cls, text: str) -> CitationType:
        """检测文献类型"""
        if cls.RE_PATENT_CN.search(text):
            return CitationType.PATENT_CN
        if cls.RE_PATENT_INTL.search(text):
            return CitationType.PATENT_INTL
        if cls.RE_TRIAL_CN.search(text) or cls.RE_TRIAL_NCT.search(text):
            return CitationType.CLINICAL_TRIAL
        if cls.RE_PREPRINT.search(text):
            return CitationType.PREPRINT
        if re.search(r'会议|Conference|Proceedings|Symposium', text,
                     re.IGNORECASE):
            return CitationType.CONFERENCE
        if re.search(r'出版社|Press|ISBN|第.*版', text):
            return CitationType.BOOK
        if re.search(r'http[s]?://', text) and not cls.RE_DOI.search(text):
            return CitationType.WEB
        # 默认期刊
        if re.search(r'[Jj]ournal|Lancet|Nature|Science|Cell|Neurology',
                     text):
            return CitationType.JOURNAL
        return CitationType.JOURNAL  # 默认为期刊

    @classmethod
    def _parse_journal_like(cls, citation: Citation, text: str):
        """解析类似期刊的引文"""
        # 尝试 GB/T 7714 格式
        gb_match = cls.RE_GB_JOURNAL.match(text)
        if gb_match:
            citation.authors = gb_match.group('authors').strip()
            citation.title = gb_match.group('title').strip()
            citation.journal = gb_match.group('journal').strip()
            citation.year = gb_match.group('year')
            if gb_match.group('vol'):
                citation.volume = gb_match.group('vol')
            if gb_match.group('issue'):
                citation.issue = gb_match.group('issue')
            if gb_match.group('pages'):
                citation.pages = gb_match.group('pages').strip()
            return

        # 尝试 Vancouver 格式
        vc_match = cls.RE_VANCOUVER.match(text)
        if vc_match:
            citation.authors = vc_match.group('authors').strip()
            citation.title = vc_match.group('title').strip()
            citation.journal = vc_match.group('journal').strip()
            citation.year = vc_match.group('year')
            if vc_match.group('vol'):
                citation.volume = vc_match.group('vol')
            if vc_match.group('issue'):
                citation.issue = vc_match.group('issue')
            if vc_match.group('pages'):
                citation.pages = vc_match.group('pages').strip()
            return

        # 简单分隔（按 ". " 分段）
        parts = text.split('. ')
        cleaned = [p.strip() for p in parts if p.strip()]

        if len(cleaned) >= 2:
            citation.authors = cleaned[0]
            citation.title = cleaned[1]
        if len(cleaned) >= 3:
            # 期刊 + 年份信息
            journal_year_part = cleaned[2]
            # 尝试从后往前匹配年份
            year_match = re.search(r'(\d{4})', journal_year_part)
            if year_match:
                citation.year = year_match.group(1)
                journal_part = journal_year_part[:year_match.start()].strip(
                    ',; '
                )
                citation.journal = journal_part

                # 查找卷期页码
                remainder = journal_year_part[year_match.end():]
                vol_issue_match = re.search(
                    r'(\d+)\s*(?:\((\d+)\))?.*?([eE]?\d+[-–][eE]?\d+)',
                    remainder
                )
                if vol_issue_match:
                    citation.volume = vol_issue_match.group(1)
                    if vol_issue_match.group(2):
                        citation.issue = vol_issue_match.group(2)
                    citation.pages = vol_issue_match.group(3)

    @classmethod
    def _parse_patent(cls, citation: Citation, text: str):
        """解析专利文献"""
        patent_match = cls.RE_PATENT_CN.search(text)
        if patent_match:
            citation.patent_number = patent_match.group()

        # 提取标题（"一种..." 或 英文标题）
        title_match = re.search(
            r'(一种.+?)(?:[，,\s]*中国|[，,\s]*CN|$)',
            text
        )
        if title_match:
            citation.title = title_match.group(1).strip()

        # 提取申请日/公开日
        app_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*申请', text)
        pub_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*公开', text)
        if app_match:
            citation.application_date = app_match.group(1)
        if pub_match:
            citation.publication_date = pub_match.group(1)

        # 提取发明人
        inventors_match = re.search(
            r'(?:发明人|Inventor)[：:]\s*(.+?)(?:[，,;；]|$)',
            text
        )
        if not inventors_match:
            # 从开头人名模式提取
            inventors_match = re.match(r'([\u4e00-\u9fff]{2,4}(?:[，,\s]+\
[\u4e00-\u9fff]{2,4})*)', text)
        if inventors_match:
            citation.authors = inventors_match.group(1).strip()

    @classmethod
    def _parse_trial(cls, citation: Citation, text: str):
        """解析临床试验备案"""
        trial_match = (cls.RE_TRIAL_CN.search(text)
                       or cls.RE_TRIAL_NCT.search(text))
        if trial_match:
            citation.trial_id = trial_match.group().replace(' ', '')

        # 解析标题/项目名称
        title_match = re.search(
            r'(?:项目|课题|研究)[名称]*[：:]\s*(.+?)(?:[，,;；]|备案|$)',
            text
        )
        if title_match:
            citation.title = title_match.group(1).strip()
        else:
            # 尝试从"XX治疗XX"模式提取
            treatment_match = re.search(
                r'(.+?治疗.+?)(?:[，,\s]*临床|$)',
                text
            )
            if treatment_match:
                citation.title = treatment_match.group(1).strip()

    @classmethod
    def _pre_validate(cls, citation: Citation):
        """预校验：检查格式问题和字段完整性"""
        issues = []

        # 检查必填字段
        if citation.ref_type in [CitationType.JOURNAL, CitationType.PREPRINT]:
            required = {
                'authors': '缺少作者信息',
                'title': '缺少标题',
                'journal': '缺少期刊名称',
                'year': '缺少年份',
            }
            for field, msg in required.items():
                if not getattr(citation, field):
                    issues.append(f"[{citation.number}] {msg}")

            # 年份格式检查
            if citation.year and not re.match(r'^\d{4}$', citation.year):
                issues.append(f"[{citation.number}] 年份格式异常: {citation.year}")

        elif citation.ref_type in [CitationType.PATENT_CN,
                                     CitationType.PATENT_INTL]:
            if not citation.patent_number:
                issues.append(f"[{citation.number}] 专利号缺失")
            if not citation.title:
                issues.append(f"[{citation.number}] 专利标题缺失")

        elif citation.ref_type == CitationType.CLINICAL_TRIAL:
            if not citation.trial_id:
                issues.append(f"[{citation.number}] 临床试验备案号缺失")

        # 作者名大小写拼写检查（常见错误）
        author_lower = citation.authors.lower()
        suspicious_patterns = [
            (r'\bmcourt\b', 'McCourt R → 可能需要大写 C'),
            (r'\bmccart\b', 'McCart → 可能需要大写 C'),
            (r'\bmacdonald\b', 'MacDonald → 可能需要大写 D'),
            (r'\bde\s+la\b', 'De La → 可能需要注意大小写'),
        ]
        for pattern, hint in suspicious_patterns:
            if re.search(pattern, author_lower):
                issues.append(f"[{citation.number}] {hint}")

        # DOI 格式检查
        if citation.doi and not citation.doi.startswith('10.'):
            issues.append(f"[{citation.number}] DOI 格式可能不正确: {citation.doi}")

        citation.issues = issues

    @classmethod
    def group_for_verification(
        cls,
        citations: list[Citation],
        group_size: int = 6
    ) -> list[list[Citation]]:
        """将引文列表分组，用于并行 Agent 验证"""
        # 按文献类型排序（期刊优先，专利/临床排后）
        type_order = {
            CitationType.JOURNAL: 0,
            CitationType.PREPRINT: 1,
            CitationType.CONFERENCE: 2,
            CitationType.BOOK: 3,
            CitationType.PATENT_CN: 4,
            CitationType.PATENT_INTL: 5,
            CitationType.CLINICAL_TRIAL: 6,
            CitationType.WEB: 7,
            CitationType.UNKNOWN: 8,
        }
        sorted_citations = sorted(
            citations,
            key=lambda c: type_order.get(c.ref_type, 9)
        )

        groups = []
        for i in range(0, len(sorted_citations), group_size):
            groups.append(sorted_citations[i:i + group_size])

        return groups

    @classmethod
    def to_summary(cls, citations: list[Citation]) -> dict:
        """生成摘要统计"""
        type_counts = {}
        for c in citations:
            t = c.ref_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        issues_count = sum(1 for c in citations if c.issues)

        return {
            'total': len(citations),
            'type_distribution': type_counts,
            'with_doi': sum(1 for c in citations if c.doi),
            'with_pmid': sum(1 for c in citations if c.pmid),
            'with_issues': issues_count,
            'total_issues': sum(len(c.issues) for c in citations),
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='科学引文预校验与格式解析工具'
    )
    parser.add_argument(
        'input',
        nargs='?',
        help='输入文件路径（省略则从 stdin 读取）'
    )
    parser.add_argument(
        '--format',
        choices=['gb', 'vancouver', 'auto'],
        default='auto',
        help='引文格式（默认自动检测）'
    )
    parser.add_argument(
        '--output',
        choices=['json', 'text', 'groups'],
        default='text',
        help='输出格式'
    )
    parser.add_argument(
        '--group-size',
        type=int,
        default=6,
        help='每组引文数量（用于并行 Agent 分组）'
    )

    args = parser.parse_args()

    # 读取输入
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    # 解析
    citations = ReferenceParser.parse_text(text)
    summary = ReferenceParser.to_summary(citations)

    # 输出
    if args.output == 'json':
        data = {
            'summary': summary,
            'citations': [asdict(c) for c in citations],
        }
        print(json.dumps(data, ensure_ascii=False, indent=2,
                         default=str))
    elif args.output == 'groups':
        groups = ReferenceParser.group_for_verification(
            citations,
            args.group_size
        )
        print(json.dumps({
            'summary': summary,
            'groups': [
                {
                    'range': f"[{g[0].number}-{g[-1].number}]",
                    'count': len(g),
                    'citation_numbers': [c.number for c in g],
                    'types': list(set(c.ref_type.value for c in g)),
                }
                for g in groups
            ],
        }, ensure_ascii=False, indent=2))
    else:
        # text 格式
        print(f"=== 引文解析报告 ===\n")
        print(f"总数: {summary['total']}")
        print(f"类型分布: {summary['type_distribution']}")
        print(f"含 DOI: {summary['with_doi']}")
        print(f"含 PMID: {summary['with_pmid']}")
        print(f"预校验问题: {summary['with_issues']}条引文共\
{summary['total_issues']}个问题\n")

        for c in citations:
            status = "✅" if not c.issues else "⚠️"
            print(f"[{c.number}] {status} {c.ref_type.value}")
            print(f"  作者: {c.authors[:60]}")
            print(f"  标题: {c.title[:80]}")
            if c.journal:
                print(f"  期刊: {c.journal}")
            print(f"  年份: {c.year} | 卷: {c.volume} | \
期: {c.issue} | 页码: {c.pages}")
            if c.doi:
                print(f"  DOI: {c.doi}")
            if c.pmid:
                print(f"  PMID: {c.pmid}")
            for issue in c.issues:
                print(f"  ⚠️ {issue}")
            print()


if __name__ == '__main__':
    main()
