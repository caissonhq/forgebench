package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.ui.Messages
import java.io.File

class ForgeBenchRepairAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val settings = ForgeBenchSettings.getInstance().state
        val repair = File(ForgeBenchCli.outputDir(project), "repair-prompt.md")
        if (!repair.exists()) {
            Messages.showWarningDialog(project, "No repair prompt found. Run a review first.", "ForgeBench")
            return
        }
        val virtual = com.intellij.openapi.vfs.LocalFileSystem.getInstance().findFileByIoFile(repair)
        if (virtual != null) {
            FileEditorManager.getInstance(project).openFile(virtual, true)
        }
        Messages.showInfoMessage(project, "Open repair-prompt.md and paste into your coding agent.", "ForgeBench repair")
    }
}