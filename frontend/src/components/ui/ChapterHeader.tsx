const VOLUME_CN = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];

interface ChapterHeaderProps {
  volume: number;
  title: string;
  className?: string;
}

export function ChapterHeader({ volume, title, className = "" }: ChapterHeaderProps) {
  return (
    <div className={`chapter-header ${className}`.trim()}>
      <span className="chapter-header-volume">卷{VOLUME_CN[volume - 1] || volume}</span>
      <span className="chapter-header-dot"> · </span>
      <span className="chapter-header-title">{title}</span>
    </div>
  );
}
