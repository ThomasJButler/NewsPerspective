export function getVisibleHeadline({
  wasRewritten,
  rewrittenTitle,
  originalTitle,
}: {
  wasRewritten: boolean;
  rewrittenTitle: string | null;
  originalTitle: string;
}): string {
  const cleanedRewrittenTitle = rewrittenTitle?.trim();

  if (wasRewritten && cleanedRewrittenTitle) {
    return cleanedRewrittenTitle;
  }

  return originalTitle;
}
