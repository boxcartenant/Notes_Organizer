var __makeTemplateObject = (this && this.__makeTemplateObject) || function (cooked, raw) {
    if (Object.defineProperty) { Object.defineProperty(cooked, "raw", { value: raw }); } else { cooked.raw = raw; }
    return cooked;
};
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { Streamlit } from "streamlit-component-lib";
import { useEffect } from "react";
import styled from "@emotion/styled";
var ButtonContainer = styled.div(templateObject_1 || (templateObject_1 = __makeTemplateObject(["\n  display: flex;\n  flex-wrap: wrap;\n  gap: 8px;\n  margin-top: 8px;\n  align-items: center;\n\n  @media (max-width: 600px) {\n    flex-direction: column;\n    align-items: flex-start;\n  }\n"], ["\n  display: flex;\n  flex-wrap: wrap;\n  gap: 8px;\n  margin-top: 8px;\n  align-items: center;\n\n  @media (max-width: 600px) {\n    flex-direction: column;\n    align-items: flex-start;\n  }\n"])));
var ActionButtons = styled.div(templateObject_2 || (templateObject_2 = __makeTemplateObject(["\n  display: flex;\n  gap: 8px;\n  flex-wrap: wrap;\n"], ["\n  display: flex;\n  gap: 8px;\n  flex-wrap: wrap;\n"])));
var MoveControls = styled.div(templateObject_3 || (templateObject_3 = __makeTemplateObject(["\n  display: flex;\n  gap: 8px;\n  align-items: center;\n  flex-wrap: wrap;\n\n  @media (min-width: 601px) {\n    margin-left: 16px;\n  }\n"], ["\n  display: flex;\n  gap: 8px;\n  align-items: center;\n  flex-wrap: wrap;\n\n  @media (min-width: 601px) {\n    margin-left: 16px;\n  }\n"])));
var Button = styled.button(templateObject_4 || (templateObject_4 = __makeTemplateObject(["\n  padding: 4px 8px;\n  font-size: 14px;\n  cursor: pointer;\n  border: 1px solid #ccc;\n  border-radius: 4px;\n  background-color: #f0f0f0;\n  &:hover {\n    background-color: #e0e0e0;\n  }\n  &:disabled {\n    cursor: not-allowed;\n    opacity: 0.5;\n  }\n"], ["\n  padding: 4px 8px;\n  font-size: 14px;\n  cursor: pointer;\n  border: 1px solid #ccc;\n  border-radius: 4px;\n  background-color: #f0f0f0;\n  &:hover {\n    background-color: #e0e0e0;\n  }\n  &:disabled {\n    cursor: not-allowed;\n    opacity: 0.5;\n  }\n"])));
var Select = styled.select(templateObject_5 || (templateObject_5 = __makeTemplateObject(["\n  padding: 4px;\n  font-size: 14px;\n  border: 1px solid #ccc;\n  border-radius: 4px;\n"], ["\n  padding: 4px;\n  font-size: 14px;\n  border: 1px solid #ccc;\n  border-radius: 4px;\n"])));
var ButtonRow = function (props) {
    var _a = props.args, blockId = _a.blockId, idx = _a.idx, chapters = _a.chapters, currentChapter = _a.currentChapter, totalBlocks = _a.totalBlocks;
    useEffect(function () {
        Streamlit.setFrameHeight();
    }, []);
    var handleAction = function (action, targetChapter) {
        Streamlit.setComponentValue({ action: action, targetChapter: targetChapter });
    };
    return (_jsxs(ButtonContainer, { children: [_jsxs(ActionButtons, { children: [_jsxs(Button, __assign({ onClick: function () { return handleAction("move_up"); }, disabled: idx === 0, title: "Swap this block with the block above it" }, { children: ["\u2B06 ", idx] })), _jsxs(Button, __assign({ onClick: function () { return handleAction("move_down"); }, disabled: idx === totalBlocks - 1, title: "Swap this block with the block below it" }, { children: ["\u2B07 ", idx] })), _jsxs(Button, __assign({ onClick: function () { return handleAction("delete"); }, title: "Delete this block" }, { children: ["\uD83D\uDDD1 ", idx] })), _jsxs(Button, __assign({ onClick: function () { return handleAction("merge"); }, disabled: idx === totalBlocks - 1, title: "Merge this block with the block below it" }, { children: ["\uD83D\uDD17 ", idx] }))] }), _jsx(MoveControls, { children: _jsxs(Select, __assign({ onChange: function (e) {
                        var targetChapter = e.target.value;
                        if (targetChapter && targetChapter !== "Select a Chapter") {
                            handleAction("move_to_chapter", targetChapter);
                        }
                    }, defaultValue: "Select a Chapter" }, { children: [_jsx("option", __assign({ value: "Select a Chapter" }, { children: "Select a Chapter" })), chapters.map(function (chapter) { return (_jsx("option", __assign({ value: chapter }, { children: chapter }), chapter)); })] })) })] }));
};
export default ButtonRow;
var templateObject_1, templateObject_2, templateObject_3, templateObject_4, templateObject_5;
