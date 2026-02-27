export type MouseButton = 'left' | 'right' | 'middle';
export type ScrollDirection = 'up' | 'down' | 'left' | 'right';
export type TabAction = 'open' | 'close' | 'switch' | 'list' | 'init' | 'refresh';
export type DialogType = 'alert' | 'confirm' | 'prompt' | 'beforeunload';
export type DialogAction = 'accept' | 'dismiss';

export interface BaseCommand {
  type: string;
  command_id?: string;
  timestamp?: number;
  tab_id?: number;
  conversation_id?: string;  // For multi-session support
}

export interface MouseMoveCommand extends BaseCommand {
  type: 'mouse_move';
  x: number;
  y: number;
  duration?: number;
}

export interface MouseClickCommand extends BaseCommand {
  type: 'mouse_click';
  button?: MouseButton;
  double?: boolean;
  count?: number;
}

export interface MouseScrollCommand extends BaseCommand {
  type: 'mouse_scroll';
  direction: ScrollDirection;
  amount: number;
}

export interface ResetMouseCommand extends BaseCommand {
  type: 'reset_mouse';
}

export interface KeyboardTypeCommand extends BaseCommand {
  type: 'keyboard_type';
  text: string;
}

export interface KeyboardPressCommand extends BaseCommand {
  type: 'keyboard_press';
  key: string;
  modifiers?: string[];
}

export interface ScreenshotCommand extends BaseCommand {
  type: 'screenshot';
  tab_id?: number;
  include_cursor?: boolean;
  quality?: number;
  include_visual_mouse?: boolean;
}

export interface TabCommand extends BaseCommand {
  type: 'tab';
  action: TabAction;
  url?: string;
  tab_id?: number;
}

export interface GetTabsCommand extends BaseCommand {
  type: 'get_tabs';
  managed_only?: boolean;
}

export interface JavascriptExecuteCommand extends BaseCommand {
  type: 'javascript_execute';
  script: string;
  return_by_value?: boolean;
  await_promise?: boolean;
  timeout?: number;
}

// Cleanup session command for multi-session support
export interface CleanupSessionCommand extends BaseCommand {
  type: 'cleanup_session';
  conversation_id: string;
}

// Handle dialog command - respond to open dialog (confirm/prompt)
export interface HandleDialogCommand extends BaseCommand {
  type: 'handle_dialog';
  action: DialogAction;  // 'accept' or 'dismiss'
  prompt_text?: string;  // Required for prompt dialogs
}

export type Command = 
  | MouseMoveCommand
  | MouseClickCommand
  | MouseScrollCommand
  | ResetMouseCommand
  | KeyboardTypeCommand
  | KeyboardPressCommand
  | ScreenshotCommand
  | TabCommand
  | GetTabsCommand
  | JavascriptExecuteCommand
  | CleanupSessionCommand
  | HandleDialogCommand;

export interface CommandResponse {
  success: boolean;
  command_id?: string;
  message?: string;
  error?: string;
  data?: any;
  timestamp: number;
  duration?: number;
  // Dialog-related fields
  dialog_opened?: boolean;
  dialog?: {
    type: DialogType;
    message: string;
    url?: string;
    needsDecision: boolean;
  };
}

export interface ScreenshotMetadata {
  imageWidth: number;
  imageHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  timestamp: number;
  tabId: number;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}