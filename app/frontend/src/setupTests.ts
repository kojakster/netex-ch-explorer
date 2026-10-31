// jsdom berechnet kein Layout; CodeMirror misst Text über diese Range-Methoden.
const emptyRects = (): DOMRectList => [] as unknown as DOMRectList;

Range.prototype.getClientRects = emptyRects;
Range.prototype.getBoundingClientRect = () => new DOMRect(0, 0, 0, 0);
