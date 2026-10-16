set -e
cd /root/props
rm -rf stage_review Must-Have-Props-Review.zip
R=stage_review/Must-Have-Props-Review
mkdir -p $R/Listing/pieces
cp src/Must-Have-Props-v1.0.zip LISTING.md review/REVIEW-CHECKLIST.md $R/
cp media/must-have-props-icon.png media/must-have-props-icon-animated.gif media/must-have-props-board-*.png $R/Listing/
cp media/must-have-props-[0-9]*.png $R/Listing/pieces/
(cd stage_review && zip -qr ../Must-Have-Props-Review.zip Must-Have-Props-Review)
ls -la Must-Have-Props-Review.zip
