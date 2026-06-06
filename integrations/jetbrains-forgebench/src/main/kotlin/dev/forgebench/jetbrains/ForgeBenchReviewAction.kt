package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.fileChooser.FileChooser
import com.intellij.openapi.fileChooser.FileChooserDescriptor
import com.intellij.openapi.ui.Messages

class ForgeBenchReviewAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val base = project.basePath ?: "."
        val diffDescriptor = FileChooserDescriptor(true, false, false, false, false, false)
            .withTitle("Select unified diff")
        val diff = FileChooser.chooseFile(diffDescriptor, project, null) ?: return
        val taskDescriptor = FileChooserDescriptor(true, false, false, false, false, false)
            .withTitle("Select task prompt")
        val task = FileChooser.chooseFile(taskDescriptor, project, null) ?: return
        val result = ForgeBenchCli.run(
            project,
            listOf(
                "review",
                "--repo", base,
                "--diff", diff.path,
                "--task", task.path,
                "--guardrails", "forgebench.yml",
            ),
        )
        if (result.exitCode != 0) {
            Messages.showErrorDialog(project, result.output, "ForgeBench review failed")
            return
        }
        Messages.showInfoMessage(project, "ForgeBench review complete.", "ForgeBench")
    }
}