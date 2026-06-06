package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class ForgeBenchStatusAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val base = project.basePath ?: "."
        val result = ForgeBenchCli.run(project, listOf("status", "--repo", base))
        if (result.exitCode == 0) {
            Messages.showInfoMessage(project, result.output, "ForgeBench status")
        } else {
            Messages.showWarningDialog(project, result.output, "ForgeBench status")
        }
    }
}