package com.example.healthcare;

import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public class RamlContractTest {
    @Test
    public void contractContainsHealthcareResources() throws IOException {
        Path contract = Path.of("..", "docs", "healthcare-api.raml");
        List<String> lines = Files.readAllLines(contract);
        String joined = String.join("\n", lines);
        Assert.assertTrue(joined.contains("/patients:"), "Patients collection missing from RAML");
        Assert.assertTrue(joined.contains("/intake/{patient_id}:"), "Intake resource missing from RAML");
    }
}
