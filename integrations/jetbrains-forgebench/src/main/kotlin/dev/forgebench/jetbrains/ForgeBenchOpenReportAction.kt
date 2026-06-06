package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.vfs.LocalFileSystem
import java.io.File

class ForgeBenchOpenReportAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val report = File(ForgeBenchCli.outputDir(project), "forgebench-report.md")
        val virtualFile = LocalFileSystem.getInstance().findFileByIoFile(report) ?: return
        FileEditorManager.getInstance(project).openFile(virtualFile, true)
    }
}