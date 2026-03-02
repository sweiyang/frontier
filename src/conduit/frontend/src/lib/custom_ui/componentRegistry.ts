import TextBlock from "./components/TextBlock.svelte";
import Button from "./components/Button.svelte";
import MetricCard from "./components/MetricCard.svelte";
import ChatWindow from "./components/ChatWindow.svelte";
import TableDisplay from "./components/TableDisplay.svelte";
import PopupBox from "./components/PopupBox.svelte";

export const registry: Record<string, any> = {
  TextBlock,
  Button,
  MetricCard,
  ChatWindow,
  TableDisplay,
  PopupBox
};
