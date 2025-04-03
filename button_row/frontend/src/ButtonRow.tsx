import { Streamlit, RenderData } from "streamlit-component-lib";
import React, { useEffect } from "react";
import styled from "@emotion/styled";

interface ButtonRowProps {
  blockId: string;
  idx: number;
  chapters: string[];
  currentChapter: string;
  totalBlocks: number;
}

// Define the shape of RenderData for streamlit-component-lib@1.2.0
interface ButtonRowRenderData {
  args: ButtonRowProps;
  disabled: boolean;
}

const ButtonContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  align-items: center;

  @media (max-width: 600px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const MoveControls = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;

  @media (min-width: 601px) {
    margin-left: 16px;
  }
`;

const Button = styled.button`
  padding: 4px 8px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #f0f0f0;
  &:hover {
    background-color: #e0e0e0;
  }
  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
`;

const Select = styled.select`
  padding: 4px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
`;

const ButtonRow: React.FC<ButtonRowRenderData> = (props) => {
  const { blockId, idx, chapters, currentChapter, totalBlocks } = props.args;

  useEffect(() => {
    Streamlit.setFrameHeight();
  }, []);

  const handleAction = (action: string, targetChapter?: string) => {
    Streamlit.setComponentValue({ action, targetChapter });
  };

  return (
    <ButtonContainer>
      <ActionButtons>
        <Button
          onClick={() => handleAction("move_up")}
          disabled={idx === 0}
          title="Swap this block with the block above it"
        >
          ⬆ {idx}
        </Button>
        <Button
          onClick={() => handleAction("move_down")}
          disabled={idx === totalBlocks - 1}
          title="Swap this block with the block below it"
        >
          ⬇ {idx}
        </Button>
        <Button
          onClick={() => handleAction("delete")}
          title="Delete this block"
        >
          🗑 {idx}
        </Button>
        <Button
          onClick={() => handleAction("merge")}
          disabled={idx === totalBlocks - 1}
          title="Merge this block with the block below it"
        >
          🔗 {idx}
        </Button>
      </ActionButtons>
      <MoveControls>
        <Select
          onChange={(e) => {
            const targetChapter = e.target.value;
            if (targetChapter && targetChapter !== "Select a Chapter") {
              handleAction("move_to_chapter", targetChapter);
            }
          }}
          defaultValue="Select a Chapter"
        >
          <option value="Select a Chapter">Select a Chapter</option>
          {chapters.map((chapter) => (
            <option key={chapter} value={chapter}>
              {chapter}
            </option>
          ))}
        </Select>
      </MoveControls>
    </ButtonContainer>
  );
};

export default ButtonRow;