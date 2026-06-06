package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages
import java.awt.Desktop
import java.io.File

class ForgeBenchExportDashboardAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val result = ForgeBenchCli.run(project, listOf("dashboard", "--repo", project.basePath ?: "."))
        if (result.exitCode != 0) {
            Messages.showErrorDialog(project, result.output, "ForgeBench dashboard export failed")
            return
        }
        val index = File(ForgeBenchCli.outputDir(project), "policy-dashboard/index.html")
        if (index.exists()) {
            Desktop.getDesktop().browse(index.toURI())
        }
        Messages.showInfoMessage(project, "Policy dashboard exported.", "ForgeBench")
    }
}